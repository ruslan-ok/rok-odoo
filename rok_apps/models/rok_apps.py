from odoo import models, fields


class RokApps(models.Model):
    _name = "rok.apps"
    _description = "Rok Apps"
    _order = "sequence asc"

    name = fields.Char(required=True)
    description = fields.Text()
    icon = fields.Char()
    active = fields.Boolean(default=True)
    sequence = fields.Integer()
