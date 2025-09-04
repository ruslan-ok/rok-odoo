from odoo import models, fields, api

class Anthropometry(models.Model):
    _name = 'rok.health.anthropometry'
    _description = 'Anthropometry'

    # The owner of the measurement; default to the current user
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        default=lambda self: self.env.user,
    )

    # Timestamp when the measurement was taken
    measurement = fields.Datetime(
        string='Date and Time of Measurement',
        required=True,
        default=fields.Datetime.now,
    )

    height = fields.Integer()
    weight = fields.Float()
    waist = fields.Float()
    temperature = fields.Float()
    systolic = fields.Float()
    diastolic = fields.Float()
    pulse = fields.Integer()
    info = fields.Html()
