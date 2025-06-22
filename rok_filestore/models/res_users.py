from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    filestore_path = fields.Char("Filestore Path")