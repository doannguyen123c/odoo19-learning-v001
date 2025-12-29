from odoo import models, fields, api, _
from odoo.exceptions import UserError

# -------------------------------------------------------------------------
# MODEL: SALE.ORDER
# -------------------------------------------------------------------------
# Đây là model chính quản lý Đơn hàng bán (Quotations/Sale Orders).
# Chúng ta sử dụng cơ chế KẾ THỪA (_inherit) để thêm tính năng vào model có sẵn của Odoo.
class SaleOrder(models.Model):
    _inherit = 'sale.order'  # Tên model gốc muốn kế thừa.

    # -------------------------------------------------------------------------
    # FIELDS (TRƯỜNG DỮ LIỆU)
    # -------------------------------------------------------------------------
    
    # fields.Boolean: Trường kiểu đúng/sai (checkbox).
    apply_virtual_vat = fields.Boolean(
        string='Xuất chênh VAT?', 
        default=False,
        help="Nếu chọn, hệ thống sẽ dùng các dòng 'Virtual VAT' để xuất hóa đơn thay vì dòng gốc."
    )
    
    # fields.One2many: Mối quan hệ 1-nhiều.
    # Một đơn hàng (sale.order) có thể có nhiều dòng ảo (sale.order.virtual.line).
    # 'order_id' là tên trường Many2one bên model con trỏ ngược về model này.
    virtual_line_ids = fields.One2many(
        'sale.order.virtual.line', 
        'order_id', 
        string='Virtual VAT Lines',
        copy=False  # Không sao chép các dòng này khi nhân bản đơn hàng.
    )

    # fields.Monetary: Trường tiền tệ (tự động xử lý tỷ giá, đơn vị tiền tệ).
    # compute='...': Trường này được tính toán tự động bởi hàm '_compute_virtual_amounts'.
    # store=True: Lưu kết quả tính toán vào database (để có thể search hoặc filter).
    virtual_amount_untaxed = fields.Monetary(string='Virtual Untaxed Amount', store=True, readonly=True, compute='_compute_virtual_amounts')
    virtual_amount_tax = fields.Monetary(string='Virtual Taxes', store=True, readonly=True, compute='_compute_virtual_amounts')
    virtual_amount_total = fields.Monetary(string='Virtual Total', store=True, readonly=True, compute='_compute_virtual_amounts')

    # -------------------------------------------------------------------------
    # COMPUTE METHODS (HÀM TÍNH TOÁN)
    # -------------------------------------------------------------------------

    # @api.depends: Decorator quan trọng!
    # Nó báo cho Odoo biết hàm này cần chạy lại khi các trường liệt kê bên trong thay đổi.
    # Ở đây: Nếu giá hoặc thuế của các dòng ảo thay đổi -> Tính lại tổng tiền.
    @api.depends('virtual_line_ids.price_subtotal', 'virtual_line_ids.price_tax', 'virtual_line_ids.price_total')
    def _compute_virtual_amounts(self):
        for order in self:
            # Tính tổng bằng Python sum() dựa trên các dòng con (recordset).
            amount_untaxed = sum(line.price_subtotal for line in order.virtual_line_ids)
            amount_tax = sum(line.price_tax for line in order.virtual_line_ids)
            amount_total = sum(line.price_total for line in order.virtual_line_ids)
            
            # Cập nhật giá trị vào record hiện tại.
            order.update({
                'virtual_amount_untaxed': amount_untaxed,
                'virtual_amount_tax': amount_tax,
                'virtual_amount_total': amount_total,
            })

    # -------------------------------------------------------------------------
    # ACTION METHODS (HÀM XỬ LÝ NÚT BẤM)
    # -------------------------------------------------------------------------

    def action_copy_to_virtual(self):
        """Sao chép các dòng bán hàng thật sang danh sách dòng ảo (Virtual Lines)."""
        self.ensure_one()  # Đảm bảo hàm chỉ chạy trên 1 bản ghi (tránh lỗi singleton).
        
        virtual_vals = []
        # Duyệt qua từng dòng bán hàng thật (order_line)
        for line in self.order_line:
            # display_type dùng để phân biệt dòng Ghi chú (Note) hoặc Tiêu đề (Section).
            # Chúng ta bỏ qua các dòng này.
            if line.display_type:
                continue
            
            # Chuẩn bị dữ liệu (dictionary) để tạo dòng mới.
            # (0, 0, {values}) là cú pháp đặc biệt của Odoo One2many để tạo mới record con.
            virtual_vals.append((0, 0, {
                'source_line_id': line.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'product_uom_qty': line.product_uom_qty,
                'product_uom_id': line.product_uom_id.id,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, line.tax_ids.ids)],  # (6, 0, [ids]) là cú pháp gán danh sách Many2many.
            }))
        
        # self.virtual_line_ids.unlink(): Xóa sạch các dòng ảo cũ trước khi tạo mới.
        self.virtual_line_ids.unlink()
        
        # Ghi dữ liệu mới vào database.
        self.write({'virtual_line_ids': virtual_vals})

    # -------------------------------------------------------------------------
    # OVERRIDES (GHI ĐÈ HÀM GỐC)
    # -------------------------------------------------------------------------

    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Ghi đè hàm tạo hóa đơn gốc của Odoo.
        Mục đích: Nếu bật 'apply_virtual_vat', ta sẽ thay thế dòng hóa đơn thật bằng dòng ảo.
        """
        # self.filtered: Lọc recordset. Tách đơn hàng thường và đơn hàng Virtual VAT.
        virtual_orders = self.filtered('apply_virtual_vat')
        standard_orders = self - virtual_orders
        
        moves = self.env['account.move'] # Khởi tạo recordset rỗng của model Account Move (Hóa đơn).

        # 1. Xử lý đơn hàng thường: Gọi logic gốc (super).
        if standard_orders:
            moves += super(SaleOrder, standard_orders)._create_invoices(grouped=grouped, final=final, date=date)

        # 2. Xử lý đơn hàng Virtual VAT
        for order in virtual_orders:
            # Kiểm tra logic nghiệp vụ: Không cho phép tạo nhiều hóa đơn nếu dùng tính năng này.
            if order.invoice_ids.filtered(lambda m: m.state != 'cancel'):
                 raise UserError(_("Virtual VAT Feature Error: Only one invoice per order is allowed. Existing invoices found for order %s.") % order.name)

            # Gọi super để Odoo tạo hóa đơn "nháp" với các thông tin cơ bản (Khách hàng, ngày tháng...).
            invoice = super(SaleOrder, order)._create_invoices(grouped=grouped, final=final, date=date)
            
            if not invoice:
                continue
                
            # QUAN TRỌNG: Xóa các dòng hóa đơn gốc mà Odoo vừa tự tạo.
            # with_context(check_move_validity=False): Tắt kiểm tra tính hợp lệ tạm thời để xóa nhanh.
            invoice.invoice_line_ids.with_context(check_move_validity=False).unlink()

            # Tạo lại các dòng hóa đơn từ dữ liệu Virtual Lines.
            new_lines_vals = []
            for v_line in order.virtual_line_ids:
                # Tìm tài khoản kế toán (Account Income) cho sản phẩm.
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
                    # Liên kết ngược lại dòng Sale Line gốc để Odoo cập nhật trạng thái "Đã xuất hóa đơn".
                    'sale_line_ids': [(6, 0, [v_line.source_line_id.id])] if v_line.source_line_id else [],
                }
                new_lines_vals.append((0, 0, vals))

            # Ghi dòng mới vào hóa đơn.
            invoice.write({'invoice_line_ids': new_lines_vals})
            
            moves += invoice

        return moves
