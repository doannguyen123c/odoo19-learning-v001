from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestComboStock(TransactionCase):
    def setUp(self):
        super(TestComboStock, self).setUp()
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderLine = self.env['sale.order.line']
        self.StockQuant = self.env['stock.quant']
        
        self.product_parent = self.env['product.product'].create({
            'name': 'Combo Parent (Storable)',
            'type': 'product', 
            'list_price': 100.0,
        })

        self.product_child = self.env['product.product'].create({
            'name': 'Combo Child (Storable)',
            'type': 'product',
            'list_price': 50.0,
        })
        
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.stock_location = self.env.ref('stock.stock_location_stock')

    def test_combo_stock_moves(self):
        so = self.SaleOrder.create({
            'partner_id': self.partner.id,
        })
        
        parent_line = self.SaleOrderLine.create({
            'order_id': so.id,
            'product_id': self.product_parent.id,
            'product_uom_qty': 1.0,
            'price_unit': 100.0,
        })
        
        child_line = self.SaleOrderLine.create({
            'order_id': so.id,
            'parent_line_id': parent_line.id,
            'is_combo_child': True,
            'product_id': self.product_child.id,
            'product_uom_qty': 5.0,
            'price_unit': 0.0,
            'tax_ids': [(6, 0, [])],
        })
        
        self.assertTrue(child_line.is_combo_child, "Child line should be marked as combo child")
        self.assertEqual(child_line.parent_line_id, parent_line, "Child should link to parent")
        self.assertEqual(child_line.price_unit, 0.0, "Child line must have 0 price")
        self.assertFalse(child_line.tax_ids, "Child line must have no taxes")
        
        so.action_confirm()
        
        self.assertTrue(so.picking_ids, "Delivery should be created")
        picking = so.picking_ids[0]
        
        moves = picking.move_ids
        
        self.assertEqual(len(moves), 1, "Delivery should contain exactly 1 stock move")
        self.assertEqual(moves.product_id, self.product_child, "Stock move should be for the child product")
        self.assertEqual(moves.product_uom_qty, 5.0, "Stock move quantity should match child line quantity")
        
        parent_moves = self.env['stock.move'].search([
            ('sale_line_id', '=', parent_line.id)
        ])
        self.assertFalse(parent_moves, "Parent line should NOT generate any stock moves")

    def test_combo_invoicing(self):
        so = self.SaleOrder.create({'partner_id': self.partner.id})
        parent_line = self.SaleOrderLine.create({
            'order_id': so.id, 
            'product_id': self.product_parent.id, 
            'product_uom_qty': 1.0, 
            'price_unit': 100.0,
        })
        child_line = self.SaleOrderLine.create({
            'order_id': so.id, 
            'parent_line_id': parent_line.id, 
            'is_combo_child': True,
            'product_id': self.product_child.id, 
            'product_uom_qty': 5.0, 
            'price_unit': 0.0,
            'tax_ids': [(6, 0, [])],
        })
        so.action_confirm()

        invoice = so._create_invoices()
        
        self.assertTrue(invoice, "Invoice should be created")
        self.assertEqual(len(invoice.invoice_line_ids), 2, "Invoice should have 2 lines (Parent + Child)")
        
        inv_parent = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_parent)
        self.assertTrue(inv_parent, "Parent line missing from invoice")
        self.assertEqual(inv_parent.price_unit, 100.0, "Parent price incorrect")
        
        inv_child = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_child)
        self.assertTrue(inv_child, "Child line missing from invoice")
        self.assertEqual(inv_child.price_unit, 0.0, "Child line price must be 0.0")
        self.assertFalse(inv_child.tax_ids, "Child line must have no taxes")
        self.assertTrue(inv_child.is_combo_child, "Child invoice line must have is_combo_child=True")
        
        self.assertEqual(invoice.amount_untaxed, 100.0, "Invoice Amount Untaxed mismatch")
        
    def test_inventory_deduction(self):
        self.StockQuant._update_available_quantity(self.product_child, self.stock_location, 10.0)
        
        so = self.SaleOrder.create({'partner_id': self.partner.id})
        parent_line = self.SaleOrderLine.create({
            'order_id': so.id, 'product_id': self.product_parent.id, 
            'product_uom_qty': 1.0, 'price_unit': 100.0
        })
        child_line = self.SaleOrderLine.create({
            'order_id': so.id, 'parent_line_id': parent_line.id, 
            'product_id': self.product_child.id, 
            'product_uom_qty': 2.0, 'price_unit': 0.0
        })
        so.action_confirm()
        
        picking = so.picking_ids[0]
        
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            
        picking.button_validate()
        
        self.product_child.invalidate_recordset()
        qty_available = self.product_child.qty_available
        self.assertEqual(qty_available, 8.0, "Inventory should be deducted by the child line quantity")