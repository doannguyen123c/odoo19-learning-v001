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
        url = 'https://bimat.2154.123corp.net/response.php'
        try:
            response = requests.get(url, timeout=10)  # Timeout 10s tránh treo
            response.raise_for_status()  # Raise error nếu HTTP không 200
            # 1. Parse JSON trực tiếp (thay vì parse text thủ công)
            try:
                data_list = response.json()
            except ValueError:
                _logger.error("Dữ liệu trả về không phải JSON hợp lệ")
                return

            if not isinstance(data_list, list):
                _logger.warning("API không trả về danh sách (List)")
                return

            # 2. Duyệt qua từng phần tử trong danh sách (PHP trả về max 5 dòng)
            count_new = 0
            for item in data_list:
                # Dữ liệu từ PHP: {'time', 'content', 'bank_account', 'received_at'}
                
                content = item.get('content', '')
                notif_time = item.get('time', '')
                bank_account = item.get('bank_account', '')

                # 3. Xử lý Transaction ID (Quan trọng)
                # Vì PHP không trả về transaction_id, ta cần tạo ID duy nhất để check trùng.
                # Cách tốt nhất: Hash MD5 của (thời gian + nội dung + tài khoản)
                unique_str = f"{notif_time}{content}{bank_account}"
                transaction_id = hashlib.md5(unique_str.encode('utf-8')).hexdigest()

                # Kiểm tra tồn tại trong DB
                existing = self.search([('transaction_id', '=', transaction_id)], limit=1)
                if existing:
                    continue # Bỏ qua nếu đã có

                # Tạo mới
                self.create({
                    'notification_time': notif_time, # Lưu ý: Cần đảm bảo format ngày tháng khớp với Odoo
                    'bank_account': bank_account,
                    'content': content,
                    'transaction_id': transaction_id, # Lưu hash ID này lại
                })
                count_new += 1
            
            if count_new > 0:
                _logger.info(f"Đã đồng bộ thành công {count_new} giao dịch mới.")

        except requests.RequestException as e:
            _logger.error("Lỗi kết nối URL %s: %s", url, e)
        except Exception as e:
            _logger.error("Lỗi xử lý dữ liệu: %s", e)
            
'''
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
            '''