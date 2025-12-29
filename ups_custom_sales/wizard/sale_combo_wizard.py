from odoo import models, fields, api

class SaleComboWizard(models.TransientModel):
    _name = 'sale.combo.wizard'
    _description = 'Add Combo Components Wizard'

    sale_order_line_id = fields.Many2one('sale.order.line', string='Parent Line', required=True, readonly=True)
    line_ids = fields.One2many('sale.combo.wizard.line', 'wizard_id', string='Components')

    def action_add_components(self):
        self.ensure_one()
        SaleOrderLine = self.env['sale.order.line']
        vals_list = []
        
        parent = self.sale_order_line_id
        current_sequence = parent.sequence

        for line in self.line_ids:
            current_sequence += 1
            vals = {
                'order_id': parent.order_id.id,
                'parent_line_id': parent.id,
                'is_combo_child': True,
                'product_id': line.product_id.id,
                'name': "  ↳ " + (line.product_id.description_sale or line.product_id.name),
                'product_uom_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'price_unit': 0.0,
                'tax_ids': [(6, 0, [])],
                'sequence': current_sequence,
            }
            vals_list.append(vals)
        
        if vals_list:
            SaleOrderLine.create(vals_list)
        
        return {'type': 'ir.actions.act_window_close'}

class SaleComboWizardLine(models.TransientModel):
    _name = 'sale.combo.wizard.line'
    _description = 'Combo Wizard Component Line'

    wizard_id = fields.Many2one('sale.combo.wizard', string='Wizard')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', compute='_compute_uom_id', store=True, readonly=False)

    @api.depends('product_id')
    def _compute_uom_id(self):
        for line in self:
            if line.product_id:
                line.uom_id = line.product_id.uom_id