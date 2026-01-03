{
    "name": "Server Folder for Documents",
    "version": "1.0",
    "depends": [
        "documents",
        "documents_spreadsheet",
    ],
    "category": "Productivity/Documents",
    "author": "Ruslan Akunevich",
    "website": "https://github.com/ruslan-ok/rok-odoo",
    "description": """
Manage document files on the server, but not as attachments.
""",
    "data": [
        "views/res_users_views.xml",
    ],
    "summary": "Manage document files on the server, but not as attachments.",
    "sequence": 48,
    "application": True,
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            "documents_server_folder/static/src/views/cog_menu/documents_cog_menu_item_refresh.js",
            "documents_server_folder/static/src/views/cog_menu/documents_cog_menu.js",
            "documents_server_folder/static/src/views/search/documents_search_model.js",
            "documents_server_folder/static/src/views/search/documents_search_panel.js",
        ],
    },
}
