from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    file_manager_path = fields.Char("Path to manage files")