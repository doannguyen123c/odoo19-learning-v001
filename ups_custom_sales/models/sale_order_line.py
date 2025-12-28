from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    parent_line_id = fields.Many2one(
        'sale.order.line', 
        string='Parent Combo Line', 
        ondelete='cascade', 
        index=True
    )
    child_line_ids = fields.One2many(
        'sale.order.line', 
        'parent_line_id', 
        string='Child Components'
    )
    is_combo_child = fields.Boolean(
        string='Is Combo Child',
        compute='_compute_is_combo_child',
        store=True
    )
    # Future-proofing for stock moves exclusion
    skip_stock_move = fields.Boolean(
        string='Skip Stock Move',
        default=False,
        help="If checked, this child line will not generate stock moves in the future."
    )

    @api.depends('parent_line_id')
    def _compute_is_combo_child(self):
        for line in self:
            line.is_combo_child = bool(line.parent_line_id)

    def _prepare_procurement_values(self):
        """
        Logic for future-proofing: if skip_stock_move is true, 
        we might return empty or modify procurement logic here.
        For now, standard Odoo behavior is maintained.
        """
        res = super()._prepare_procurement_values()
        return res

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Override to prevent stock moves for Combo Parent lines.
        Only children should generate moves.
        """
        # Filter out lines that are Combo Parents (have children AND are marked as combo)
        # We check 'child_line_ids' to be sure it successfully expanded.
        # We also respect 'skip_stock_move' for future proofing.
        lines_to_process = self.filtered(
            lambda line: not (line.product_id.is_ups_combo and line.child_line_ids) and not line.skip_stock_move
        )
        return super(SaleOrderLine, lines_to_process)._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            # Avoid processing if it's already a child or imported with children
            if line.parent_line_id:
                continue

            # Check if this line is a parent combo product
            # Access product_tmpl_id via product_id
            if line.product_id and line.product_id.product_tmpl_id.is_ups_combo:
                 # Only expand if children haven't been created (e.g. by manual duplication)
                if not line.child_line_ids:
                    line._create_combo_children()
        return lines

    def _create_combo_children(self):
        self.ensure_one()
        vals_list = []
        for component in self.product_id.product_tmpl_id.combo_line_ids:
            # Basic values for the component line
            vals = {
                'order_id': self.order_id.id,
                'parent_line_id': self.id,
                'product_id': component.component_id.id,
                'name': "  ↳ " + (component.component_id.description_sale or component.component_id.name), # Visual indentation
                'product_uom_qty': self.product_uom_qty * component.quantity,
                'product_uom_id': component.uom_id.id or component.component_id.uom_id.id,
                'price_unit': 0.0,
                'tax_ids': [(6, 0, [])], # No taxes on zero price components
                'sequence': self.sequence, # Same sequence to stay close, or +1
                'skip_stock_move': False, # Children DO generate stock moves as per requirement
            }
            vals_list.append(vals)
        
        if vals_list:
            # We call create() again. 
            # Recursion is naturally limited because components shouldn't be 'is_ups_combo' 
            # (or if they are, they will expand too, which is correct).
            self.env['sale.order.line'].create(vals_list)

    def write(self, values):
        """
        Override write to handle:
        1. Quantity updates (sync to children).
        2. Product changes (re-explode).
        """
        # Logic 1: Sync Quantity
        if 'product_uom_qty' in values:
            for line in self:
                if line.child_line_ids:
                    # Calculate ratio or just re-compute based on component definition?
                    # Safer to re-compute based on component definition to avoid drift.
                    # But we need to map children to components.
                    # Simplest approach: Update child qty proportionally if we assume 1:1 map, 
                    # OR delete and recreate children (cleaner but risky if stock moves exist).
                    # Given stock moves might exist, we SHOULD update quantity on existing lines if possible.
                    
                    # For now, let's update proportionally based on the new parent qty.
                    # Constraint: This assumes the child structure hasn't been manually messed with.
                    ratio = values['product_uom_qty'] / (line.product_uom_qty or 1.0)
                    if line.product_uom_qty == 0:
                        # Edge case: increasing from 0. We can't use ratio.
                        # We should re-read the component qty.
                        pass 
                    
                    # Better approach: Loop children and match with product component? 
                    # If we just update 'product_uom_qty' on children, Odoo handles the stock move update.
                    
                    # Implementation:
                    # We will loop children and re-calculate expected qty.
                    # This relies on the child still being linked to a component def. 
                    # But we don't have a direct link to 'product.combo.line'.
                    # So we update proportionally.
                     for child in line.child_line_ids:
                         # We need the original component ratio.
                         # We can try to find the component in the parent's product template
                         # matching the child's product.
                         comp_line = line.product_id.product_tmpl_id.combo_line_ids.filtered(
                             lambda c: c.component_id == child.product_id
                         )
                         if comp_line:
                             # If multiple lines for same product, we take the first. Limitation known.
                             new_child_qty = values['product_uom_qty'] * comp_line[0].quantity
                             child.write({'product_uom_qty': new_child_qty})

        result = super().write(values)

        # Logic 2: Product Change (Parent changed product)
        if 'product_id' in values:
            for line in self:
                if line.child_line_ids:
                    # If product changed, old children are invalid.
                    # We must unlink them. 
                    # Note: cascading delete usually works on record deletion, not field change.
                    # So we manually unlink.
                    line.child_line_ids.unlink()
                    
                # Re-explode if new product is a combo
                if line.product_id.product_tmpl_id.is_ups_combo:
                     line._create_combo_children()

        return result

    def unlink(self):
        """
        Prevent manual deletion of combo children.
        """
        for line in self:
            if line.is_combo_child:
                raise UserError(_("You cannot delete a combo component line directly. Please delete the parent line: %s") % line.parent_line_id.name)
        return super().unlink()

    def _compute_qty_to_invoice(self):
        """
        Override to exclude combo children from invoicing.
        """
        super()._compute_qty_to_invoice()
        for line in self:
            if line.is_combo_child:
                line.qty_to_invoice = 0.0