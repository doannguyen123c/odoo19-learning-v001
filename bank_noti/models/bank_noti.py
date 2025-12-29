from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import requests
import logging
import hashlib
from datetime import datetime
import random

_logger = logging.getLogger(__name__) # Khởi tạo logger để ghi log vào hệ thống.

# -------------------------------------------------------------------------
# MODEL: BANK.NOTI
# -------------------------------------------------------------------------
# Model lưu trữ thông báo biến động số dư ngân hàng.
class BankNoti(models.Model):
    _name = 'bank.noti'          # Tên kỹ thuật của model (lưu trong DB là bank_noti).
    _description = 'Bank Notification'
    _order = 'notification_time desc' # Sắp xếp mặc định: Mới nhất lên đầu.

    # Các trường dữ liệu cơ bản
    notification_time = fields.Datetime(string='Thời gian thông báo')
    bank_account = fields.Char(string='Tài khoản ngân hàng')
    amount = fields.Integer(string='Số tiền')
    content = fields.Text(string='Nội dung')
    
    # index=True: Tạo chỉ mục tìm kiếm nhanh trong database.
    transaction_id = fields.Char(string='Transaction ID', index=True)

    # _sql_constraints: Ràng buộc cấp database.
    # Đảm bảo transaction_id là duy nhất, không trùng lặp.
    _sql_constraints = [
        ('transaction_id_unique', 'UNIQUE(transaction_id)', 'Transaction ID đã tồn tại!')
    ]
    
    # -------------------------------------------------------------------------
    # SECURITY METHODS
    # -------------------------------------------------------------------------
    
    def unlink(self):
        """
        Ghi đè hàm xóa (unlink).
        Chỉ cho phép người dùng thuộc nhóm Quản trị viên hệ thống (base.group_system) xóa.
        """
        # self.env.user: Truy cập user đang thực hiện hành động.
        # has_group(): Kiểm tra quyền.
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Chỉ có quản trị viên mới được phép xóa thông báo ngân hàng.'))
        return super(BankNoti, self).unlink()

    # -------------------------------------------------------------------------
    # CRON JOB / SCHEDULED ACTION
    # -------------------------------------------------------------------------

    @api.model
    def fetch_bank_notifications(self):
        """
        Hàm này được gọi tự động bởi Cron Job (định kỳ).
        Nhiệm vụ: Gọi API lấy sao kê và lưu vào Odoo.
        """
        USE_DEMO_DATA = False # Cờ chuyển đổi chế độ Demo/Real.
        
        count_new = 0
        
        if USE_DEMO_DATA:
            # Logic tạo dữ liệu giả lập (dành cho dev/test).
            _logger.info("Chạy ở chế độ DEMO - Tạo dữ liệu giả lập để test cron")
            
            demo_data_list = [
                {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'content': f'Tài khoản nhận được {random.randint(1000000, 10000000)} VND từ chuyển khoản',
                    'bank_account': '1234567890',
                    'amount': random.randint(500000, 5000000),
                    'transaction_id': str(random.randint(500000, 5000000)),
                },
                # ... (thêm data mẫu)
            ]
            data_list = demo_data_list
            
        else:
            # Logic gọi API thật.
            url = 'https://bimat.2154.123corp.net/response.php'
            try:
                # requests.get: Thư viện Python để gọi HTTP GET.
                response = requests.get(url, timeout=15)
                response.raise_for_status() # Báo lỗi nếu HTTP status != 200.
                
                data_list = response.json() # Parse JSON trả về.
                if not isinstance(data_list, list):
                    _logger.warning("API không trả về danh sách JSON")
                    return
                
            except requests.RequestException as e:
                _logger.error("Lỗi kết nối URL %s: %s", url, e)
                return
            except ValueError:
                _logger.error("Dữ liệu trả về không phải JSON hợp lệ")
                return
            except Exception as e:
                _logger.error("Lỗi xử lý response: %s", e)
                return

        # Duyệt qua danh sách data lấy được.
        for item in data_list:
            # .get(): Lấy giá trị từ dict an toàn (tránh lỗi KeyError).
            notif_time_str = item.get('time', False)
            content = item.get('content', '')
            amount = item.get('amount', '')
            bank_account = item.get('bank_account', '')
            transaction_id = item.get('transaction_id', '')

            # Validate dữ liệu cơ bản.
            if not notif_time_str or not content or not bank_account:
                continue

            # Kiểm tra trùng lặp (Idempotency check).
            # search([], limit=1): Tìm xem đã có record nào trùng transaction_id chưa.
            if self.search([('transaction_id', '=', transaction_id)], limit=1):
                continue

            # Tạo bản ghi mới.
            self.create({
                'notification_time': notif_time_str,
                'bank_account': bank_account,
                'amount': amount,
                'content': content,
                'transaction_id': transaction_id,
            })
            count_new += 1

        # Ghi log kết quả.
        if count_new > 0:
            _logger.info(f"Đồng bộ thành công: {count_new} thông báo mới được tạo.")
        else:
            _logger.info("Không có thông báo mới (hoặc tất cả đã tồn tại).")
