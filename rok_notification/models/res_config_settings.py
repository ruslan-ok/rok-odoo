from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    telegram_token = fields.Char(
        string='Telegram Bot Token',
        config_parameter='rok_notification.telegram_token',
        help='Bot token used for Telegram notifications from Calendar.'
    )


