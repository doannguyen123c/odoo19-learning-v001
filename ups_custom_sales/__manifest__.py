{
    'name': 'UPS Custom Sales',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Virtual VAT Invoicing and Dynamic Product Combos',
    'author': 'Diego Nguyen',
    'depends': ['sale', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'wizard/sale_combo_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}