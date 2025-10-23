from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    kcal_100g = fields.Integer(string="Energy, kcal/100g")
