{
    'name': 'Migrator',
    'version': '1.0',
    'depends': ['rok_all'],
    'category': 'Tools',
    'description': 'Migrator',
    'data': [
        "data/rok_migration_root.xml",
        'security/ir.model.access.csv',
        'views/rok_migration_views.xml',
    ],
    'installable': True,
    'author': 'Ruslan Akunevich',
    "license": "LGPL-3",
}