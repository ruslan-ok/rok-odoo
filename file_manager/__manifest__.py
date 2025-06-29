{
    "name": "File Manager",
    "version": "1.0",
    "depends": [
        "base",
        "mail",
    ],
    "category": "Productivity",
    "author": "Ruslan Akunevich",
    "website": "https://github.com/ruslan-ok/rok-odoo",
    "description": """
Managing files on the server
""",
    "data": [
        "security/ir.model.access.csv",
        "data/ir_actions_data.xml",
        "views/file_manager_views.xml",
        "views/file_manager_menu.xml",
        "views/res_users_views.xml",
    ],

    "summary": "Managing files on the server",
    "sequence": 48,
    "application": True,
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            "file_manager/static/src/xml/**/*",
            "file_manager/static/src/components/**/*",
            "file_manager/static/src/js/file_manager_controller.js",
            "file_manager/static/src/js/file_manager_renderers.js",
            "file_manager/static/src/js/file_manager_views.js",
            "file_manager/static/src/js/file_manager_utils.js",
            "file_manager/static/src/scss/file_manager_common.scss",
            "file_manager/static/src/scss/file_manager_views.scss",
            "file_manager/static/src/scss/file_manager_editor.scss",
        ],
        "web.assets_backend_lazy_dark": [
            "file_manager/static/src/scss/file_manager_views.dark.scss",
        ],
        "web.assets_web_dark": [
            "file_manager/static/src/scss/file_manager_views.dark.scss",
        ],
        "web.assets_frontend": [
            "file_manager/static/src/scss/file_manager_common.scss",
            "file_manager/static/src/js/file_manager_utils.js",
        ],
        "web.assets_web_print": [
            "file_manager/static/src/scss/file_manager_print.scss",
        ]
    },
}
