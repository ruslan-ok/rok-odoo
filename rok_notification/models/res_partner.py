from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    telegram_chat_id = fields.Char(
        string='Telegram Chat ID',
        help='Telegram chat ID used for sending notifications to this partner.'
    )


