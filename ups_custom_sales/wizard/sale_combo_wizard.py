from odoo import models, fields, api

# -------------------------------------------------------------------------
# WIZARD: SALE.COMBO.WIZARD
# -------------------------------------------------------------------------
# TransientModel: Model tạm thời. Dữ liệu trong này sẽ tự động bị xóa sau một thời gian.
# Thường dùng cho các hộp thoại (Dialog/Wizard).
class SaleComboWizard(models.TransientModel):
    _name = 'sale.combo.wizard'
    _description = 'Add Combo Components Wizard'

    # Dòng cha đang được chọn để thêm combo.
    sale_order_line_id = fields.Many2one('sale.order.line', string='Parent Line', required=True, readonly=True)
    
    # Danh sách các thành phần con sẽ thêm.
    line_ids = fields.One2many('sale.combo.wizard.line', 'wizard_id', string='Components')

    def action_add_components(self):
        """Hàm xử lý khi bấm nút 'Add' trên Wizard."""
        self.ensure_one()
        SaleOrderLine = self.env['sale.order.line'] # Lấy model sale.order.line từ môi trường (env).
        vals_list = []
        
        parent = self.sale_order_line_id
        current_sequence = parent.sequence # Lấy thứ tự sắp xếp của dòng cha.

        for line in self.line_ids:
            current_sequence += 1 # Tăng thứ tự để dòng con nằm ngay dưới dòng cha.
            
            # Chuẩn bị dữ liệu tạo dòng con.
            vals = {
                'order_id': parent.order_id.id,       # Thuộc cùng đơn hàng với cha.
                'parent_line_id': parent.id,          # Link với cha.
                'is_combo_child': True,               # Đánh dấu là con.
                'product_id': line.product_id.id,
                # Thêm dấu thụt đầu dòng (indentation) để đẹp UI.
                'name': "  ↳ " + (line.product_id.description_sale or line.product_id.name),
                'product_uom_qty': line.quantity,
                'product_uom_id': line.uom_id.id,
                'price_unit': 0.0,                    # Giá bằng 0 (vì giá nằm ở cha).
                'tax_ids': [(6, 0, [])],              # Không chịu thuế (thuế nằm ở cha).
                'sequence': current_sequence,
            }
            vals_list.append(vals)
        
        # Tạo hàng loạt các dòng con.
        if vals_list:
            SaleOrderLine.create(vals_list)
        
        # Đóng wizard sau khi xong.
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
        """Tự động lấy đơn vị tính mặc định của sản phẩm khi chọn sản phẩm."""
        for line in self:
            if line.product_id:
                line.uom_id = line.product_id.uom_id
