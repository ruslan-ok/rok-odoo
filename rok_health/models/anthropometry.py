from odoo import models, fields, api

class Anthropometry(models.Model):
    _name = 'rok.health.anthropometry'
    _description = 'Anthropometry'
    _order = 'measurement desc'

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

    height = fields.Integer(group_operator='avg')
    weight = fields.Float(group_operator='avg')
    waist = fields.Float(group_operator='avg')
    temperature = fields.Float(group_operator='avg')
    systolic = fields.Float(group_operator='avg')
    diastolic = fields.Float(group_operator='avg')
    pulse = fields.Integer(group_operator='avg')
    info = fields.Html()
