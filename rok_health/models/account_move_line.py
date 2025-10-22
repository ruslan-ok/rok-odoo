from odoo import models, fields, api, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    weight_g = fields.Integer(string='Weight, grams')
    pack_pcs = fields.Float(string='Pack Volume, pieces')
    kcal_100g = fields.Integer(string='Calories in 100 grams')
