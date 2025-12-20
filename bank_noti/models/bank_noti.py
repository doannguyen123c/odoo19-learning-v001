# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)

class BankNoti(models.Model):
    _name = 'bank.noti'
    _description = 'Bank Notification'
    _order = 'notification_time desc'

    notification_time = fields.Datetime(string='Thời gian thông báo')
    bank_account = fields.Char(string='Tài khoản ngân hàng')  # Hoặc Integer nếu là số
    content = fields.Text(string='Nội dung')
    transaction_id = fields.Char(string='Transaction ID', index=True)

    _sql_constraints = [
        ('transaction_id_unique', 'UNIQUE(transaction_id)', 'Transaction ID đã tồn tại!')
    ]

    @api.model
    def fetch_bank_notifications(self):
        """Method gọi từ cron để poll URL và insert nếu mới"""
        url = 'https://bankstatus.vn/response.php'
        try:
            response = requests.get(url, timeout=10)  # Timeout 10s tránh treo
            response.raise_for_status()  # Raise error nếu HTTP không 200

            # Endpoint trả về PHP array print → cần parse thủ công (không phải JSON chuẩn)
            text = response.text.strip()
            if not text.startswith("array("):
                _logger.warning("Response không phải array PHP: %s", text)
                return

            # Parse đơn giản bằng eval (an toàn vì format cố định)
            data_str = text[6:-1]  # Bỏ "array(" và ")"
            items = {}
            for part in data_str.split(','):
                if '=>' in part:
                    key, value = part.split('=>', 1)
                    key = key.strip().strip("'\"")
                    value = value.strip().strip("'\"")
                    items[key] = value

            transaction_id = items.get('transaction_id')
            if not transaction_id:
                _logger.warning("Không có transaction_id trong response")
                return

            # Kiểm tra tồn tại
            existing = self.search([('transaction_id', '=', transaction_id)], limit=1)
            if existing:
                _logger.info("Bỏ qua transaction_id đã tồn tại: %s", transaction_id)
                return

            # Tạo mới
            self.create({
                'notification_time': items.get('time'),
                'bank_account': items.get('bank_account'),
                'content': items.get('content'),
                'transaction_id': transaction_id,
            })
            _logger.info("Tạo mới thông báo ngân hàng: %s", transaction_id)

        except requests.RequestException as e:
            _logger.error("Lỗi khi fetch URL %s: %s", url, e)
        except Exception as e:
            _logger.error("Lỗi parse/insert dữ liệu: %s", e)