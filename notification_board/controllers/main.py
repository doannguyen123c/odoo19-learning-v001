from odoo import http
from odoo.http import request

# -------------------------------------------------------------------------
# CONTROLLER: WEB ROUTES
# -------------------------------------------------------------------------
# Controller xử lý các yêu cầu HTTP từ trình duyệt (Web Frontend).
class NotificationBoardController(http.Controller):
    
    # @http.route: Định nghĩa URL (endpoint) cho trang web.
    # type='http': Trả về HTML (webpage).
    # auth="user": Yêu cầu người dùng phải đăng nhập mới truy cập được.
    # website=True: Bật các tính năng website (menu, footer, session...).
    @http.route(['/notification_board', '/notification_board/page/<int:page>'], type='http', auth="user", website=True)
    def notification_list(self, page=1, **kw):
        """Trang danh sách thông báo (có phân trang)."""
        NotificationBoard = request.env['notification.board'] # Truy cập model từ request.env.
        domain = [('is_published', '=', True)] # Chỉ lấy tin đã xuất bản.
        
        # Cấu hình phân trang (Pagination).
        page_count = 10 # Số tin mỗi trang.
        notification_count = NotificationBoard.search_count(domain) # Đếm tổng số tin.
        
        # request.website.pager: Hàm tiện ích của Odoo để tạo thanh phân trang HTML.
        pager = request.website.pager(
            url='/notification_board',
            total=notification_count,
            page=page,
            step=page_count,
            scope=7,
            url_args=kw
        )
        
        # Lấy dữ liệu cho trang hiện tại.
        notifications = NotificationBoard.search(
            domain,
            limit=page_count,
            offset=pager['offset'],
            order='create_date desc'
        )
        
        # values: Dữ liệu truyền vào template QWeb để hiển thị.
        values = {
            'notifications': notifications,
            'pager': pager,
        }
        # request.render: Render template XML thành HTML và trả về trình duyệt.
        return request.render('notification_board.notification_list', values)

    @http.route('/notification_board/<int:notification_id>', type='http', auth="user", website=True)
    def notification_detail(self, notification_id, **kw):
        """Trang chi tiết một thông báo."""
        # .browse(id): Lấy record theo ID.
        notification = request.env['notification.board'].browse(notification_id)
        
        # Kiểm tra tồn tại và quyền xem.
        if not notification.exists() or not notification.is_published:
            return request.redirect('/notification_board')
            
        # Đánh dấu đã đọc (nếu dùng tính năng mail.thread).
        # sudo(): Dùng quyền admin để ghi đè quyền truy cập (nếu user thường không có quyền sửa).
        if notification.sudo().message_needaction:
            notification.sudo().message_set_read(notification.ids)
            
        values = {
            'notification': notification,
        }
        return request.render('notification_board.notification_detail', values)
