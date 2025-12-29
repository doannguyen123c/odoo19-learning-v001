from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_combo_child = fields.Boolean(
        string='Is Combo Child',
        compute='_compute_is_combo_child',
        store=True,
        help="Technical flag derived from the source sale order line to identify combo components."
    )

    @api.depends('sale_line_ids.is_combo_child')
    def _compute_is_combo_child(self):
        for line in self:
            line.is_combo_child = any(line.is_combo_child for line in line.sale_line_ids)