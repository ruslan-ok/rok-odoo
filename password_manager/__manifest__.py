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
        "views/passwords_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "assets": {
        "web.assets_backend": [
            "passwords/static/src/views/**/*",
        ],
    },
    "license": "LGPL-3",
}
