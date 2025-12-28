from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_ups_combo = fields.Boolean(string='Is Combo Product', default=False)
    combo_line_ids = fields.One2many('product.combo.line', 'product_tmpl_id', string='Combo Components')

class ProductComboLine(models.Model):
    _name = 'product.combo.line'
    _description = 'Product Combo Component'

    product_tmpl_id = fields.Many2one('product.template', string='Parent Product', required=True, ondelete='cascade')
    component_id = fields.Many2one('product.product', string='Component', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
