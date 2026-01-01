{
    'name': 'Notification Board',
    'version': '19.0.1.1.0',
    'summary': 'Company News & Announcements Board',
    'description': """
        A centralized blog-like system for internal company announcements.
        
        Features:
        - Rich Text Editor for articles (images, fonts, formatting).
        - Comments and social features (Chatter).
        - Tagging system.
        - Access Control: Only Administrators can post; Users can read & comment.
    """,
    'category': 'Productivity/Communication',
    'author': 'Diego Nguyen',
    'depends': ['base', 'mail', 'website'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/notification_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
