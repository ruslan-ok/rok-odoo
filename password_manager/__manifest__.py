{
    "name": "Password Manager",
    "version": "2.0",
    "summary": "Password Manager",
    "sequence": 46,
    "description": "Password Manager",
    "category": "Productivity",
    "website": "https://github.com/ruslan-ok/rok-odoo",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/passwords_security.xml",
        "views/passwords_views.xml",
        "views/password_category_views.xml",
    ],
    "application": True,
    "assets": {
        "web.assets_backend": [
            "password_manager/static/src/views/**/*",
            "password_manager/static/src/css/passwords_tree.css",
        ],
    },
    "external_dependencies": {
        "python": ["cryptography"],
    },
    "author": "Ruslan Akunevich",
    "license": "LGPL-3",
}
