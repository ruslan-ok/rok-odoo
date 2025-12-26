from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    kcal_100g = fields.Integer(string="Energy, kcal/100g")
