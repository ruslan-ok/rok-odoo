from odoo import models, fields


class PasswordHistory(models.Model):
    _name = "password.history"
    _description = "Password History"
    _order = "password_id, create_date desc"

    password_id = fields.Many2one("passwords", ondelete="cascade")
    value = fields.Char()
