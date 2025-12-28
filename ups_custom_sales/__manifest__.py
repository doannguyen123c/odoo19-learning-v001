{
    'name': 'UPS Custom Sales',
    'version': '1.0',
    'category': 'Sales',
    'author': 'Diego Nguyen',
    'summary': 'Virtual VAT Invoicing and Dynamic Product Combos',
    'depends': ['sale', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
