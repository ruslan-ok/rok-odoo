{
    "name": "Rok Apps",
    "version": "1.0",
    "summary": "Rok Apps module",
    "author": "Ruslan Akunevich",
    "license": "LGPL-3",
    "website": "https://ventor.tech",
    "application": True,
    "category": "Productivity/Rok Apps",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/rok_apps_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "rok_apps/static/src/rok_apps_widget_registry.js",
            "rok_apps/static/src/rok_apps_widget.js",
            "rok_apps/static/src/rok_apps_widget.xml",
            "rok_apps/static/src/rok_apps_widget.scss",
            "rok_apps/static/src/kanban_compiler.js",
            "rok_apps/static/src/kanban_record.js",
            "rok_apps/static/src/kanban_renderer.js",
        ],
    },
}
