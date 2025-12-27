from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    weight_g = fields.Integer(string="Weight, grams")
    pack_pcs = fields.Float(string="Pack Volume, pieces")
    kcal_100g = fields.Integer(string="Calories in 100 grams")

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if (
            self.product_id
            and self.move_id.move_type == "in_invoice"
            and self.product_id.categ_id == self.env.ref("rok_health.cat_food")
        ):
            self.weight_g = self.product_id.weight
            self.pack_pcs = self.product_id.volume
            self.kcal_100g = self.product_id.kcal_100g
            self.price_unit = self.product_id.standard_price
