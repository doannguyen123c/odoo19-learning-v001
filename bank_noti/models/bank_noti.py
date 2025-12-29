from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import requests
import logging
import hashlib
from datetime import datetime
import random

_logger = logging.getLogger(__name__)

class BankNoti(models.Model):
    _name = 'bank.noti'
    _description = 'Bank Notification'
    _order = 'notification_time desc'

    notification_time = fields.Datetime(string='Thời gian thông báo')
    bank_account = fields.Char(string='Tài khoản ngân hàng')
    amount = fields.Integer(string='Số tiền')
    content = fields.Text(string='Nội dung')
    transaction_id = fields.Char(string='Transaction ID', index=True)

    _sql_constraints = [
        ('transaction_id_unique', 'UNIQUE(transaction_id)', 'Transaction ID đã tồn tại!')
    ]
    
    def unlink(self):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Chỉ có quản trị viên mới được phép xóa thông báo ngân hàng.'))
        return super(BankNoti, self).unlink()

    @api.model
    def fetch_bank_notifications(self):
        USE_DEMO_DATA = False
        
        count_new = 0
        
        if USE_DEMO_DATA:
            _logger.info("Chạy ở chế độ DEMO - Tạo dữ liệu giả lập để test cron")
            
            demo_data_list = [
                {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'content': f'Tài khoản nhận được {random.randint(1000000, 10000000)} VND từ chuyển khoản',
                    'bank_account': '1234567890',
                    'amount': random.randint(500000, 5000000),
                    'transaction_id': str(random.randint(500000, 5000000)),
                },
                {
                    'time': (datetime.now().replace(minute=(datetime.now().minute - 5) % 60)).strftime('%Y-%m-%d %H:%M:%S'),
                    'content': f'Chuyển khoản thành công {random.randint(500000, 5000000)} VND',
                    'bank_account': '0987654321',
                    'amount': random.randint(500000, 5000000),
                    'transaction_id': str(random.randint(500000, 5000000)),
                },
            ]
            
            data_list = demo_data_list
            
        else:
            url = 'https://bimat.2154.123corp.net/response.php'
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                
                data_list = response.json()
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

        for item in data_list:
            notif_time_str = item.get('time', False)
            content = item.get('content', '')
            amount = item.get('amount', '')
            bank_account = item.get('bank_account', '')
            transaction_id = item.get('transaction_id', '')

            if not notif_time_str or not content or not bank_account:
                continue

            if self.search([('transaction_id', '=', transaction_id)], limit=1):
                continue

            self.create({
                'notification_time': notif_time_str,
                'bank_account': bank_account,
                'amount': amount,
                'content': content,
                'transaction_id': transaction_id,
            })
            count_new += 1

        if count_new > 0:
            _logger.info(f"Đồng bộ thành công: {count_new} thông báo mới được tạo.")
        else:
            _logger.info("Không có thông báo mới (hoặc tất cả đã tồn tại).")