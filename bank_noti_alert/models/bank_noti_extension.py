# -*- coding: utf-8 -*-
from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.tools import Markup
except ImportError:
    from markupsafe import Markup

class BankNoti(models.Model):
    _inherit = 'bank.noti'

    @api.model_create_multi
    def create(self, vals_list):
        # Create records normally
        records = super(BankNoti, self).create(vals_list)
        
        # Logic to notify users
        # Try to find the 'BankNoti' channel
        channel = self.env['discuss.channel'].search([('name', 'ilike', 'BankNoti')], limit=1)
        
        # Fallback if 'BankNoti' isn't found, pick the first available channel
        if not channel:
            channel = self.env['discuss.channel'].search([], limit=1)

        if channel:
            _logger.info("Bank Noti Alert: Found channel '%s' for notifications.", channel.name)
            for record in records:
                amount_formatted = f"{record.amount:,.0f}" if record.amount else "0"
                
                # Use Markup to render HTML tags correctly.
                msg_body = Markup(
                    "<p>📢 <b>New Bank Transaction Detected</b></p>"
                    "<ul style='list-style-type: none; padding-left: 0;'>"
                    "<li>💰 <b>Amount:</b> %s</li>"
                    "<li>📝 <b>Content:</b> %s</li>"
                    "<li>🏦 <b>Account:</b> %s</li>"
                    "</ul>"
                ) % (amount_formatted, record.content or 'N/A', record.bank_account or 'N/A')
                
                channel.message_post(
                    body=msg_body,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
                
        return records