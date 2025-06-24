{
    "name": "Rok Filestore Owl",
    "version": "1.0",
    "summary": "Representation of file system folders",
    "sequence": 47,
    "description": """
Representation of file system folders
""",
    "category": "Productivity",
    "website": "https://github.com/ruslan-ok/rok-odoo",
    "depends": ["web"],
    "data": [
        "views/filestore_menu.xml",
        "views/res_users_views.xml",
    ],
    "application": True,
    "assets": {
        "web.assets_backend": [
            "rok_filestore_owl/static/src/js/**/*.js",
            "rok_filestore_owl/static/src/js/templates/**/*.xml",
        ],
    },
    "author": "Ruslan Akunevich",
    "license": "LGPL-3",
}
