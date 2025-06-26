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
        "data/ir_actions_data.xml",
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
            "rok_filestore_qweb/static/src/xml/**/*",
            "rok_filestore_qweb/static/src/components/**/*",
            "rok_filestore_qweb/static/src/js/filestore_controller.js",
            "rok_filestore_qweb/static/src/js/filestore_renderers.js",
            "rok_filestore_qweb/static/src/js/filestore_views.js",
            "rok_filestore_qweb/static/src/js/filestore_utils.js",
            "rok_filestore_qweb/static/src/scss/filestore_common.scss",
            "rok_filestore_qweb/static/src/scss/filestore_views.scss",
            "rok_filestore_qweb/static/src/scss/filestore_editor.scss",
        ],
        "web.assets_backend_lazy_dark": [
            "rok_filestore_qweb/static/src/scss/filestore_views.dark.scss",
        ],
        "web.assets_web_dark": [
            "rok_filestore_qweb/static/src/scss/filestore_views.dark.scss",
        ],
        "web.assets_frontend": [
            "rok_filestore_qweb/static/src/scss/filestore_common.scss",
            "rok_filestore_qweb/static/src/js/filestore_utils.js",
        ],
        "web.assets_web_print": [
            "rok_filestore_qweb/static/src/scss/filestore_print.scss",
        ]
    },
}
