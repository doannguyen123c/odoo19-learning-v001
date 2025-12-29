# Odoo Project: Custom Sales & Notifications
**Author:** Diego Nguyen  
**Odoo Version:** 19.0 (Developer Preview / Master)

Dự án này bao gồm các modules tùy chỉnh (custom addons) cho hệ thống Odoo ERP, tập trung vào quy trình Bán hàng (Sales), Kế toán (Accounting) và Truyền thông nội bộ (Internal Communication).

---

## 📂 Cấu Trúc Thư Mục

Dự án bao gồm các module chính nằm trong thư mục `addons/`:

1.  **`ups_custom_sales`**: (Module Chính)
    *   **Tính năng:** Tùy biến quy trình bán hàng nâng cao.
    *   **Combo Sản phẩm (Dynamic Combos):** Cho phép tạo gói sản phẩm linh động ngay trên đơn hàng, tách biệt giá bán (ở dòng cha) và tồn kho (ở dòng con).
    *   **Virtual VAT (Hóa đơn ảo):** Cơ chế tách biệt dòng hàng thực tế và dòng hàng xuất hóa đơn đỏ (VAT) để phục vụ kế toán thuế.
2.  **`bank_noti`**:
    *   **Tính năng:** Tự động đồng bộ thông báo biến động số dư ngân hàng qua API hoặc Cron Job.
3.  **`bank_noti_alert`**:
    *   **Tính năng:** Mở rộng module `bank_noti` để bắn thông báo vào kênh Chat (Discuss) khi có tiền về.
4.  **`notification_board`**:
    *   **Tính năng:** Bảng tin nội bộ (như Blog/News) cho công ty, tích hợp Website Portal cho nhân viên xem tin tức.

---

## 📚 Kiến Thức Odoo Cơ Bản (Cho Người Mới)

Nếu bạn là người mới học Odoo, dưới đây là các khái niệm quan trọng được sử dụng trong mã nguồn:

### 1. ORM (Object-Relational Mapping)
Odoo sử dụng ORM để thao tác với database thay vì viết SQL thuần.
*   **Model (`models.Model`):** Đại diện cho một bảng trong database. Ví dụ: `sale.order` là bảng đơn hàng.
*   **Recordset:** Tập hợp các bản ghi dữ liệu. Bạn có thể lặp qua nó (`for record in self`) như một list trong Python.
*   **Fields:** Các cột dữ liệu.
    *   `Char`, `Integer`, `Boolean`: Các kiểu dữ liệu cơ bản.
    *   `Many2one`, `One2many`: Quan hệ giữa các bảng (Ví dụ: Một đơn hàng có nhiều dòng chi tiết).
    *   `Monetary`: Kiểu tiền tệ, tự động xử lý ký hiệu tiền tệ (VND, USD).

### 2. Kế thừa (Inheritance)
Odoo rất mạnh ở khả năng mở rộng. Trong dự án này, chúng ta dùng `_inherit` rất nhiều.
*   **Ví dụ:** `_inherit = 'sale.order'` trong `ups_custom_sales`.
*   **Ý nghĩa:** Chúng ta không sửa file gốc của Odoo. Chúng ta tạo một file mới, kế thừa lại nó và thêm trường mới hoặc ghi đè hàm cũ. Điều này giúp dễ dàng nâng cấp Odoo sau này.

### 3. Decorators Thường Dùng
*   `@api.depends('field_a', 'field_b')`: Dùng cho hàm tính toán (`compute`). Khi `field_a` hoặc `field_b` đổi giá trị, hàm này tự chạy lại để tính giá trị mới.
*   `@api.model`: Dùng cho các hàm không cần record cụ thể (ví dụ: Cron job chạy ngầm).
*   `@http.route`: Dùng trong Controller để định nghĩa đường dẫn URL cho Website.

### 4. Views & XML
Giao diện người dùng trong Odoo được định nghĩa bằng XML.
*   **Tree/List View:** Danh sách bản ghi.
*   **Form View:** Form nhập liệu chi tiết.
*   **XPath:** Công cụ để chèn nút bấm hoặc trường dữ liệu vào vị trí bất kỳ trong View có sẵn của Odoo.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### Yêu cầu hệ thống
*   Python 3.10 trở lên.
*   PostgreSQL 14 trở lên.
*   Odoo 19 (Source code hoặc Docker).

### Các bước thiết lập
1.  **Clone Source Code:**
    ```bash
    git clone <repo_url>
    cd odoo19v001
    ```
2.  **Cấu hình Odoo (`odoo.conf`):**
    Đảm bảo đường dẫn `addons_path` trỏ tới thư mục `addons` của dự án này.
    ```ini
    addons_path = /path/to/odoo/addons,/path/to/project/addons
    ```
3.  **Khởi động Odoo:**
    ```bash
    python odoo-bin -c odoo.conf -d <database_name> -u ups_custom_sales
    ```
    *(Tham số `-u` giúp update/cài đặt module ngay khi chạy)*.

4.  **Kích hoạt tính năng:**
    *   Vào menu **Apps**, tìm "UPS Custom Sales" và bấm **Install**.
    *   Các module phụ thuộc (`sale`, `account`, `stock`) sẽ tự động được cài đặt.

---

## 💡 Lưu Ý Khi Phát Triển
*   **Code Style:** Tuân thủ chuẩn PEP8 của Python.
*   **Security:** Luôn định nghĩa quyền truy cập trong `ir.model.access.csv`.
*   **Comments:** Mã nguồn đã được chú thích chi tiết bằng tiếng Việt, hãy đọc kỹ các file `.py` để hiểu logic nghiệp vụ.

**Chúc bạn học tốt Odoo!**
