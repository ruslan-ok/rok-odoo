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
    direction = fields.Selection([
        ('consumed', 'Consumed'),
        ('burned', 'Burned'),
    ], required=True, default='consumed')
    product_id = fields.Many2one('product.product', string='Product')
    consumed_g = fields.Integer(string="Consumed grams")
    consumed_pcs = fields.Float(string="Consumed pieces")
    pack_g = fields.Integer(string="Pack Weight, grams")
    pack_pcs = fields.Float(string="Pack Volume, pieces")
    kcal_100g = fields.Integer(string='Calories in 100 grams')
    consumed_kcal = fields.Integer(compute='_compute_calories_consumed', store=True)
    burned_kcal = fields.Integer(string='Burned calories')
    activity = fields.Selection([
        ('cycling', 'Cycling'),
        ('walking', 'Walking'),
        ('other', 'Other'),
    ], required=True, default='cycling')
    distance = fields.Float(string='Distance, km')
    info = fields.Html()

    @api.depends('direction', 'kcal_100g', 'consumed_g', 'consumed_pcs', 'pack_g', 'pack_pcs', 'burned_kcal')
    def _compute_calories_consumed(self):
        for record in self:
            match record.direction:
                case 'burned':
                    record.consumed_kcal = -record.burned_kcal or 0
                case 'consumed':
                    kcal_100g = record.kcal_100g or 0
                    consumed_g = record.consumed_g or 0
                    consumed_pcs = record.consumed_pcs or 0
                    pack_g = record.pack_g or 0
                    pack_pcs = record.pack_pcs or 0

                    if kcal_100g and consumed_g:
                        record.consumed_kcal = kcal_100g * consumed_g / 100
                    elif consumed_pcs and pack_g and pack_pcs and kcal_100g:
                        record.consumed_kcal = pack_g / 100 * kcal_100g / pack_pcs * consumed_pcs
                    else:
                        record.consumed_kcal = 0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.pack_g = self.product_id.weight
            self.pack_pcs = self.product_id.volume
            self.kcal_100g = self.product_id.kcal_100g