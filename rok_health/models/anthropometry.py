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

    height = fields.Integer(aggregator='avg')
    weight = fields.Float(aggregator='avg')
    waist = fields.Float(aggregator='avg')
    temperature = fields.Float(aggregator='avg')
    systolic = fields.Float(aggregator='avg')
    diastolic = fields.Float(aggregator='avg')
    pulse = fields.Integer(aggregator='avg')
    info = fields.Html()
