from odoo import fields, models


class PasswordGeneratorHistory(models.Model):
    _name = "password.history"
    _description = "Password History"

    value = fields.Char()
    password_id = fields.Many2one("passwords", "Password",)
