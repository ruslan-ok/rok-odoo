from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    weight = fields.Integer(string="Weight, grams")
    volume = fields.Integer(string="Volume, pieces")
    kcal_100g = fields.Integer(string="Energy, kcal/100g")
