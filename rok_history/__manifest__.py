{
    "name": "Rok History",
    "summary": "History module for the Rok Project",
    "category": "Productivity/Health",
    "version": "1.0",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/rok_history_rules.xml",
        "views/rok_history_views.xml",
        "views/rok_history_category_views.xml",
    ],
    "installable": True,
    "application": True,
    "author": "Ruslan Akunevich",
    "license": "LGPL-3",
}
