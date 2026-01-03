# -*- coding: utf-8 -*-
{
    'name': 'Project Gantt Dashboard',
    'version': '19.0.1.0.1',
    'summary': 'Interactive Gantt Chart for Project Management (Community)',
    'description': """
        Project Gantt Dashboard (Odoo Community)
        ========================================
        
        Key Features:
        - **Timeline View:** Visualize tasks by project on a Gantt timeline.
        - **Interactive:** Drag & drop to reschedule (Update Start Date & Deadline).
        - **Data Integrity:** "Soft Visualization" for missing dates, strict Odoo access control.
        - **Integration:** Seamless link to standard Task Form Views.
        
        Tech Stack: Owl Framework + Frappe Gantt JS.
    """,
    'category': 'Project Management',
    'author': 'Diego Nguyen',
    'license': 'LGPL-3',
    'depends': [
        'project',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_views.xml',
        'views/gantt_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # External Libraries (Frappe Gantt)
            'project_gantt_dashboard/static/lib/frappe_gantt.css',
            'project_gantt_dashboard/static/lib/frappe_gantt.js',
            
            # Owl Components, Services & Styles
            'project_gantt_dashboard/static/src/components/gantt_dashboard.scss',
            'project_gantt_dashboard/static/src/services/gantt_data_service.js',
            'project_gantt_dashboard/static/src/components/gantt_dashboard.js',
            'project_gantt_dashboard/static/src/components/gantt_dashboard.xml',
            'project_gantt_dashboard/static/src/main.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
