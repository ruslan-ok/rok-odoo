from odoo import models, fields, api

class Calories(models.Model):
    _name = 'calories'
    _description = 'Calories consumption'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        default=lambda self: self.env.user,
    )
    event_dt = fields.Datetime(
        string='Event Datetime',
        required=True,
        index=True,
        default=lambda self: fields.Datetime.now(),
    )
    product_id = fields.Many2one('product.product', string='Product')
    consumed_g = fields.Integer(string="Consumed grams")
    consumed_pcs = fields.Float(string="Consumed pieces")
    pack_g = fields.Integer(string="Pack Weight, grams")
    pack_pcs = fields.Float(string="Pack Volume, pieces")
    kcal_100g = fields.Integer(string='Calories in 100 grams')
    consumed_kcal = fields.Integer(compute='_compute_calories_consumed')
    info = fields.Html()

    @api.depends('kcal_100g', 'consumed_g', 'consumed_pcs', 'pack_g', 'pack_pcs')
    def _compute_calories_consumed(self):
        for record in self:
            if record.kcal_100g * record.consumed_g:
                record.consumed_kcal = record.kcal_100g * record.consumed_g / 100
            elif record.consumed_pcs * record.pack_g * record.pack_pcs * record.kcal_100g:
                record.consumed_kcal = record.pack_g / 100 * record.kcal_100g / record.pack_pcs * record.consumed_pcs
            else:
                record.consumed_kcal = 0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.pack_g = self.product_id.weight
            self.pack_pcs = self.product_id.volume
            self.kcal_100g = self.product_id.kcal_100g