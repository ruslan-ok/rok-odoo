{
    'name': 'Rok Health',
    'summary': 'Health module for the Rok Project',
    'category': 'Productivity/Health',
    'version': '1.0',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/rok_health_rules.xml',
        'views/anthropometry_views.xml',
    ],
    'installable': True,
    'application': True,
    'author': 'Ruslan Akunevich',
    'license': 'LGPL-3',
}
