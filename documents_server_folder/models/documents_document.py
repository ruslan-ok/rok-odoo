from odoo import models, api, _

class Document(models.Model):
    _inherit = "documents.document"

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        result = super().search_panel_select_range(field_name)
        my_server_folder = {
            "bold": True, 
            "childrenIds": [], 
            "parentId": False, 
            "user_permission": "edit",
            "display_name": _("My Server Folder"),
            "id": "MY_FOLDER",
            "user_permission": "edit",
            "description": _("Your individual space on the Server."),
        }
        for i in range(len(result["values"]) - 1, -1, -1):
            if result["values"][i].get("id") == "MY":
                result["values"].insert(i + 1, my_server_folder)
                break
        return result
