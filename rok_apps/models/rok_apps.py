from odoo import models, fields


class RokApps(models.Model):
    _name = "rok.apps"
    _description = "Rok Apps"

    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    icon = fields.Char(string="Icon")
    active = fields.Boolean(string="Active")
