{
    'name': 'Bank Noti',
    'version': '19.0.1.0.0',
    'summary': 'Hiển thị thông báo ngân hàng',
    'description': """
        Module hiển thị danh sách thông báo ngân hàng.
        Chỉ đọc, không thêm/sửa/xóa.
    """,
    'author': 'Diego Nguyen',
    'category': 'Accounting',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/bank_noti_views.xml',
    ],
    'installable': True,
    'application': True,  # Hiển thị như một App riêng trong menu Apps
    'auto_install': False,
}