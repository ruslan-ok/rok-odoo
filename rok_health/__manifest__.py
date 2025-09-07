{
    'name': 'Rok Health',
    'summary': 'Health module for the Rok Project',
    'category': 'Productivity/Health',
    'version': '1.0',
    'depends': [
        'base',
        'spreadsheet_dashboard',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/rok_health_rules.xml',
        'views/anthropometry_views.xml',
        'views/dashboard_anthropometry.xml',
    ],
    'installable': True,
    'application': False,
    'author': 'Ruslan Akunevich',
    'license': 'LGPL-3',
}
