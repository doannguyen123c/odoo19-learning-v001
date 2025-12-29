from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    apply_virtual_vat = fields.Boolean(
        string='Xuất chênh VAT?', 
        default=False,
        help="If checked, the system will use 'Virtual VAT' lines for invoicing instead of standard lines."
    )
    
    virtual_line_ids = fields.One2many(
        'sale.order.virtual.line', 
        'order_id', 
        string='Virtual VAT Lines',
        copy=False
    )

    virtual_amount_untaxed = fields.Monetary(string='Virtual Untaxed Amount', store=True, readonly=True, compute='_compute_virtual_amounts')
    virtual_amount_tax = fields.Monetary(string='Virtual Taxes', store=True, readonly=True, compute='_compute_virtual_amounts')
    virtual_amount_total = fields.Monetary(string='Virtual Total', store=True, readonly=True, compute='_compute_virtual_amounts')

    @api.depends('virtual_line_ids.price_subtotal', 'virtual_line_ids.price_tax', 'virtual_line_ids.price_total')
    def _compute_virtual_amounts(self):
        for order in self:
            amount_untaxed = sum(line.price_subtotal for line in order.virtual_line_ids)
            amount_tax = sum(line.price_tax for line in order.virtual_line_ids)
            amount_total = sum(line.price_total for line in order.virtual_line_ids)
            
            order.update({
                'virtual_amount_untaxed': amount_untaxed,
                'virtual_amount_tax': amount_tax,
                'virtual_amount_total': amount_total,
            })

    def action_copy_to_virtual(self):
        self.ensure_one()
        virtual_vals = []
        for line in self.order_line:
            if line.display_type:
                continue
                
            virtual_vals.append((0, 0, {
                'source_line_id': line.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'product_uom_qty': line.product_uom_qty,
                'product_uom_id': line.product_uom_id.id,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, line.tax_ids.ids)],
            }))
        
        self.virtual_line_ids.unlink()
        self.write({'virtual_line_ids': virtual_vals})

    def _create_invoices(self, grouped=False, final=False, date=None):
        virtual_orders = self.filtered('apply_virtual_vat')
        standard_orders = self - virtual_orders
        
        moves = self.env['account.move']

        if standard_orders:
            moves += super(SaleOrder, standard_orders)._create_invoices(grouped=grouped, final=final, date=date)

        for order in virtual_orders:
            if order.invoice_ids.filtered(lambda m: m.state != 'cancel'):
                 raise UserError(_("Virtual VAT Feature Error: Only one invoice per order is allowed. Existing invoices found for order %s.") % order.name)

            invoice = super(SaleOrder, order)._create_invoices(grouped=grouped, final=final, date=date)
            
            if not invoice:
                continue
                
            invoice.invoice_line_ids.with_context(check_move_validity=False).unlink()

            new_lines_vals = []
            for v_line in order.virtual_line_ids:
                product = v_line.product_id
                account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(_('Please define an income account for product: %s') % product.name)

                vals = {
                    'name': v_line.name,
                    'quantity': v_line.product_uom_qty,
                    'price_unit': v_line.price_unit,
                    'product_id': v_line.product_id.id,
                    'product_uom_id': v_line.product_uom_id.id,
                    'tax_ids': [(6, 0, v_line.tax_ids.ids)],
                    'account_id': account.id,
                    'sale_line_ids': [(6, 0, [v_line.source_line_id.id])] if v_line.source_line_id else [],
                }
                new_lines_vals.append((0, 0, vals))

            invoice.write({'invoice_line_ids': new_lines_vals})
            
            moves += invoice

        return moves