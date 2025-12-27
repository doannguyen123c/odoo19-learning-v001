{
    'name': 'Bank Notification Alert',
    'version': '19.0.1.0.0',
    'summary': 'Post a message to General channel when a new bank notification is received',
    'description': """
        Extends the Bank Noti module to alert users via the Discuss app (General channel)
        whenever a new bank transaction is created.
    """,
    'author': 'Diego Nguyen',
    'category': 'Accounting',
    'depends': ['base', 'bank_noti', 'mail'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': True,
}