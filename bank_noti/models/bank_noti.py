from odoo import models, fields

class BankNoti(models.Model):
    _name = 'bank.noti'
    _description = 'Thông báo Ngân hàng'
    _order = 'notification_time desc'  # Sắp xếp mới nhất lên đầu

    notification_time = fields.Datetime(string='Thời gian', required=True)
    bank_account = fields.Char(string='Tài khoản Ngân hàng', required=True)
    transction_id = fields.Char(string='Mã giao dịch', required=True)
    content = fields.Text(string='Nội dung', required=True)