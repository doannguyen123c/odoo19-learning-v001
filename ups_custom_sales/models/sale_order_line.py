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
        default=False,
        index=True
    )
    is_combo_parent = fields.Boolean(
        string='Is Combo Parent',
        compute='_compute_is_combo_parent',
        help="Technical flag for UI styling to identify parent lines with components."
    )

    @api.depends('child_line_ids')
    def _compute_is_combo_parent(self):
        for line in self:
            line.is_combo_parent = bool(line.child_line_ids)

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        lines_to_process = self.filtered(lambda line: not line.child_line_ids)
        return super(SaleOrderLine, lines_to_process)._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)

    def action_open_combo_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Combo Components'),
            'res_model': 'sale.combo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_line_id': self.id},
        }