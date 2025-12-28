from odoo import models, fields, api

class SaleOrderVirtualLine(models.Model):
    _name = 'sale.order.virtual.line'
    _description = 'Sale Order Virtual VAT Line'

    order_id = fields.Many2one('sale.order', string='Order Reference', required=True, ondelete='cascade')
    source_line_id = fields.Many2one('sale.order.line', string='Source Sales Line', ondelete='set null')
    
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Text(string='Description', required=True)
    
    product_uom_qty = fields.Float(string='Quantity', default=1.0, digits='Product Unit of Measure')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    
    price_unit = fields.Float(string='Virtual Unit Price', digits='Product Price', default=0.0)
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)
    
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True, string='Currency')
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, index=True)

    @api.depends('product_uom_qty', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        for line in self:
            taxes = line.tax_ids.compute_all(
                line.price_unit, 
                line.order_id.currency_id, 
                line.product_uom_qty, 
                product=line.product_id, 
                partner=line.order_id.partner_shipping_id
            )
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes.get('total_included'),
                'price_subtotal': taxes.get('total_excluded'),
            })