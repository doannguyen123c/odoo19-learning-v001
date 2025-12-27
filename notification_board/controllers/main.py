from odoo import http
from odoo.http import request

class NotificationBoardController(http.Controller):
    @http.route(['/notification_board', '/notification_board/page/<int:page>'], type='http', auth="user", website=True)
    def notification_list(self, page=1, **kw):
        NotificationBoard = request.env['notification.board']
        domain = [('is_published', '=', True)]
        
        # Pagination
        page_count = 10  # Number of notifications per page
        notification_count = NotificationBoard.search_count(domain)
        pager = request.website.pager(
            url='/notification_board',
            total=notification_count,
            page=page,
            step=page_count,
            scope=7,
            url_args=kw
        )
        
        notifications = NotificationBoard.search(
            domain,
            limit=page_count,
            offset=pager['offset'],
            order='create_date desc'
        )
        
        values = {
            'notifications': notifications,
            'pager': pager,
        }
        return request.render('notification_board.notification_list', values)

    @http.route('/notification_board/<int:notification_id>', type='http', auth="user", website=True)
    def notification_detail(self, notification_id, **kw):
        notification = request.env['notification.board'].browse(notification_id)
        if not notification.exists() or not notification.is_published:
            return request.redirect('/notification_board')
            
        # Mark as read if the current user hasn't read it yet
        if notification.sudo().message_needaction:
            notification.sudo().message_set_read(notification.ids)
            
        values = {
            'notification': notification,
        }
        return request.render('notification_board.notification_detail', values)
