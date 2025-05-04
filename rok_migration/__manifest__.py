{
    "name": "Rok Migration",
    "version": "1.0",
    "summary": "Rok Migration",
    "sequence": 30,
    "description": """
Migrating data from rok-apps server.
""",
    "category": "Productivity/Knowledge",
    "website": "https://github.com/ruslan-ok/rok-odoo",
    "depends": [
        "knowledge", 
        "password_manager",
        "documents",
    ],
    "data": [
        "data/ir_actions_data.xml",
        "views/knowledge_menus.xml",
        "views/passwords_menus.xml",
        "views/documents_menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "assets": {},
    "license": "LGPL-3",
}
