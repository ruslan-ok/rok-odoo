{
    "name": "Password Manager",
    "version": "1.0",
    "summary": "Password Manager",
    "sequence": 20,
    "description": """
Password Manager
""",
    "category": "Productivity",
    "website": "https://github.com/ruslan-ok/rok-odoo",
    "depends": ["base", "mail"],
    "data": [
        "data/password_data.xml",
        "security/ir.model.access.csv",
        "security/passwords_security.xml",
        "views/passwords_views.xml",
        "views/password_category_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "assets": {
        "web.assets_backend": [
            "password_manager/static/src/views/**/*",
        ],
    },
    "license": "LGPL-3",
}
