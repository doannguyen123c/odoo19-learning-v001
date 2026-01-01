# -*- coding: utf-8 -*-
from datetime import datetime, date

from markupsafe import escape

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_ui_order_id_html = fields.Html(
        string='Order ID',
        compute='_compute_ui_html_fields',
        store=False,
        sanitize=False,
    )
    x_ui_customer_html = fields.Html(
        string='Khách hàng',
        compute='_compute_ui_html_fields',
        store=False,
        sanitize=False,
    )
    x_ui_products_html = fields.Html(
        string='Sản phẩm',
        compute='_compute_ui_html_fields',
        store=False,
        sanitize=False,
    )
    x_ui_state_badge_html = fields.Html(
        string='Trạng thái',
        compute='_compute_ui_html_fields',
        store=False,
        sanitize=False,
    )

    @api.depends('name', 'state', 'partner_id', 'client_order_ref', 'order_line')
    def _compute_ui_html_fields(self):
        for order in self:
            order.x_ui_order_id_html = order._get_ui_order_id_html()
            order.x_ui_customer_html = order._get_ui_customer_html()
            order.x_ui_products_html = order._get_ui_products_html()
            order.x_ui_state_badge_html = order._get_ui_state_badge_html()

    def _get_ui_order_id_html(self):
        self.ensure_one()
        category = self._get_order_category_label()
        order_name = escape(self.name or '-')

        return (
            "<div style='display:flex; gap:8px; align-items:flex-start;'>"
            "<span style='display:inline-block; width:8px; height:8px; margin-top:6px; "
            "border-radius:50%%; background:#2e86de;'></span>"
            "<div style='line-height:1.2;'>"
            "<div style='font-size:11px; color:#6b7280;'>%s</div>"
            "<div style='font-size:13px; color:#1a5fb4; font-weight:600;'>%s</div>"
            "</div>"
            "</div>"
        ) % (escape(category), order_name)

    def _get_ui_customer_html(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            return ''

        company_name = partner.commercial_company_name or partner.name or ''
        contact_name = partner.name or ''
        if company_name == contact_name:
            contact_name = ''

        phone = partner.phone or getattr(partner, 'mobile', '') or ''
        address = partner.contact_address or self._format_partner_address(partner)

        ref = self.client_order_ref or ''
        delivery_date = self._get_delivery_date()

        contact_line = ''
        if contact_name or phone:
            contact_line = '%s%s' % (
                escape(contact_name) if contact_name else '',
                (' - ' + escape(phone)) if phone else '',
            )

        return (
            "<div style='line-height:1.25;'>"
            "<div style='font-weight:600;'>%s</div>"
            "%s"
            "%s"
            "%s"
            "%s"
            "</div>"
        ) % (
            escape(company_name),
            ("<div style='color:#374151; font-size:12px;'>%s</div>" % contact_line) if contact_line else '',
            ("<div style='color:#6b7280; font-size:12px;'>%s</div>" % escape(address)) if address else '',
            ("<div style='color:#7c3aed; font-size:12px;'>PO: %s</div>" % escape(ref)) if ref else '',
            ("<div style='color:#dc2626; font-size:12px;'>Giao: %s</div>" % escape(delivery_date)) if delivery_date else '',
        )

    def _get_ui_products_html(self):
        self.ensure_one()
        lines = self.order_line.filtered(lambda l: not l.display_type)
        if not lines:
            return ''

        items = []
        total_lines = len(lines)
        for line in lines[:4]:
            name = line.product_id.display_name or line.name or ''
            qty_str = '%g' % (line.product_uom_qty or 0.0)
            items.append(
                "<li style='margin:0 0 2px 0;'>%s <span style='color:#d64541; font-weight:600;'>x%s</span></li>"
                % (escape(name), escape(qty_str))
            )

        if total_lines > 4:
            more_count = total_lines - 4
            items.append(
                "<li style='color:#6b7280;'>+ %s more...</li>" % escape(str(more_count))
            )

        return (
            "<ul style='margin:0; padding-left:16px;'>%s</ul>" % ''.join(items)
        )

    def _get_ui_state_badge_html(self):
        self.ensure_one()
        state_map = {
            'draft': ('Vừa mới tạo', '#1e40af', '#dbeafe'),
            'sent': ('Vừa mới tạo', '#1e40af', '#dbeafe'),
            'sale': ('Sales Order', '#047857', '#d1fae5'),
            'done': ('Đã giao hàng', '#c2410c', '#ffedd5'),
            'cancel': ('Đã hủy', '#b91c1c', '#fee2e2'),
        }
        label, text_color, bg_color = state_map.get(self.state, (self.state or '', '#111827', '#e5e7eb'))
        return (
            "<span style='display:inline-block; padding:2px 8px; border-radius:999px; "
            "font-size:12px; font-weight:600; color:%s; background:%s;'>%s</span>"
        ) % (escape(text_color), escape(bg_color), escape(label))

    def _get_order_category_label(self):
        self.ensure_one()
        label = ''
        if 'tag_ids' in self._fields and self.tag_ids:
            label = self.tag_ids[0].name

        if not label:
            for line in self.order_line.filtered(lambda l: not l.display_type):
                categ = line.product_id.categ_id
                if categ:
                    label = categ.name
                    break

        return label or 'Chưa phân loại'

    def _format_partner_address(self, partner):
        parts = [
            partner.street,
            partner.street2,
            partner.city,
            partner.state_id.name if partner.state_id else '',
            partner.zip,
            partner.country_id.name if partner.country_id else '',
        ]
        parts = [p for p in parts if p]
        return ', '.join(parts)

    def _get_delivery_date(self):
        self.ensure_one()
        value = self.commitment_date
        if not value and 'expected_date' in self._fields:
            value = self.expected_date
        if not value:
            return ''

        if isinstance(value, datetime):
            value = fields.Datetime.context_timestamp(self, value)
            return value.strftime('%d/%m/%Y')
        if isinstance(value, date):
            return value.strftime('%d/%m/%Y')
        return str(value)
