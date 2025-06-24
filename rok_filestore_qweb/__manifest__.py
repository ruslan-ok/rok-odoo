{
    "name": "Rok Filestore QWeb",
    "version": "1.0",
    "depends": ["base"],
    "category": "Productivity",
    "author": "Ruslan Akunevich",
    "website": "https://github.com/ruslan-ok/rok-odoo",
    "description": """
Representation of file system folders
""",
    "data": [
        "security/ir.model.access.csv",
        "views/rok_filestore_views.xml",
        "views/rok_filestore_menu.xml",
    ],

    "summary": "Representation of file system folders",
    "sequence": 48,
    "category": "Productivity",
    "application": True,
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            'rok_filestore_qweb/static/src/xml/**/*',
            'rok_filestore_qweb/static/src/components/**/*',
            "rok_filestore_qweb/static/src/js/filestore_controller.js",
            "rok_filestore_qweb/static/src/js/filestore_renderers.js",
            "rok_filestore_qweb/static/src/js/filestore_views.js",
        ],
    },

}
