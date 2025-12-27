from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        res = super()._post(soft)
        cat_food = self.env.ref("rok_health.cat_food")
        for record in self.filtered(lambda record: record.move_type == "in_invoice"):
            for line in record.line_ids.filtered(
                lambda line: line.product_id.categ_id == cat_food,
            ):
                line.product_id.write(
                    {
                        "weight": line.weight_g,
                        "volume": line.pack_pcs,
                        "kcal_100g": line.kcal_100g,
                        "standard_price": line.price_unit,
                    },
                )
        return res
