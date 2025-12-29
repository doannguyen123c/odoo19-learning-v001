from odoo import models, fields, api, _
from odoo.exceptions import UserError

# -------------------------------------------------------------------------
# MODEL: SALE.ORDER.LINE
# -------------------------------------------------------------------------
# Kế thừa dòng chi tiết đơn hàng để thêm tính năng Combo Sản phẩm.
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # -------------------------------------------------------------------------
    # FIELDS (QUẢN LÝ COMBO)
    # -------------------------------------------------------------------------
    
    # Liên kết đệ quy (Self-referencing):
    # Một dòng cha (Parent) chứa nhiều dòng con (Children).
    # parent_line_id: Dòng này thuộc về combo nào?
    parent_line_id = fields.Many2one(
        'sale.order.line', 
        string='Parent Combo Line', 
        ondelete='cascade', # Nếu xóa cha, xóa luôn con.
        index=True
    )
    
    # child_line_ids: Các thành phần con của dòng này.
    child_line_ids = fields.One2many(
        'sale.order.line', 
        'parent_line_id', 
        string='Child Components'
    )
    
    # Cờ đánh dấu dòng này là dòng con.
    is_combo_child = fields.Boolean(
        string='Is Combo Child',
        default=False,
        index=True
    )
    
    # Cờ đánh dấu dòng này là dòng cha (để tô đậm UI).
    # compute: Trường này được tính toán, không lưu cứng (trừ khi có store=True).
    is_combo_parent = fields.Boolean(
        string='Is Combo Parent',
        compute='_compute_is_combo_parent',
        help="Technical flag for UI styling to identify parent lines with components."
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('child_line_ids')
    def _compute_is_combo_parent(self):
        for line in self:
            # Nếu dòng có chứa dòng con (child_line_ids không rỗng) -> Là Parent.
            line.is_combo_parent = bool(line.child_line_ids)

    # -------------------------------------------------------------------------
    # STOCK LOGIC (QUAN TRỌNG)
    # -------------------------------------------------------------------------

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Ghi đè logic tạo phiếu kho (Delivery Order).
        
        Quy tắc nghiệp vụ:
        1. Dòng Combo Cha: Chỉ mang giá tiền, KHÔNG xuất kho.
        2. Dòng Combo Con: Không có giá tiền, NHƯNG PHẢI xuất kho.
        """
        # Lọc ra các dòng cần xử lý kho:
        # Chỉ giữ lại dòng KHÔNG phải là Combo Parent (tức là dòng thường hoặc dòng con).
        # Combo Parent (có child_line_ids) sẽ bị loại bỏ khỏi danh sách 'lines_to_process'.
        lines_to_process = self.filtered(lambda line: not line.child_line_ids)
        
        # Gọi hàm gốc (super) với danh sách đã lọc.
        return super(SaleOrderLine, lines_to_process)._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)

    # -------------------------------------------------------------------------
    # UI ACTIONS
    # -------------------------------------------------------------------------

    def action_open_combo_wizard(self):
        """Mở Wizard để chọn thành phần combo cho dòng hiện tại."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', # Kiểu action: Mở cửa sổ.
            'name': _('Add Combo Components'), # Tiêu đề cửa sổ.
            'res_model': 'sale.combo.wizard',  # Model của Wizard.
            'view_mode': 'form',
            'target': 'new', # Mở dạng popup (modal).
            'context': {'default_sale_order_line_id': self.id}, # Truyền ID dòng hiện tại vào wizard.
        }
