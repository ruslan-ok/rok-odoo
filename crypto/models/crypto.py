from odoo import models, fields

class Crypto(models.TransientModel):
    _name = 'rok.crypto'
    _description = 'Crypto'

    dt = fields.Datetime(string='Datetime')
    value = fields.Float(string='Value', aggregator='avg')
