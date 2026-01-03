from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    server_folder_path = fields.Char("Server Folder with Documents")
