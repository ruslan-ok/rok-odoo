{
    "name": "Crypto",
    "version": "1.0",
    "summary": "Crypto module",
    "author": "Ruslan Akunevich",
    "license": "LGPL-3",
    "website": "https://github.com/ruslan-ok/rok-odoo",
    "application": False,
    "category": "Productivity/Crypto",
    "depends": [
        "rok_apps",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/crypto_view.xml",
        "data/rok_apps.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "crypto/static/src/components/report_view_periods.js",
            "crypto/static/src/components/report_view_periods.xml",
            "crypto/static/src/components/crypto.scss",
            "crypto/static/src/components/crypto.js",
            "crypto/static/src/components/crypto.xml",
            "crypto/static/src/rok_apps_widget.js",
            "crypto/static/src/rok_apps_widget.xml",
            "crypto/static/src/rok_apps_widget.scss",
        ],
        "web.assets_backend_lazy": [
            "crypto/static/src/components/crypto_model.js",
            "crypto/static/src/views/graph/crypto_graph.js",
            "crypto/static/src/views/graph/crypto_graph.xml",
        ],
    },
}
