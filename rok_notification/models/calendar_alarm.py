from odoo import fields, models


class CalendarAlarm(models.Model):
    _inherit = 'calendar.alarm'

    alarm_type = fields.Selection(selection_add=[
        ('telegram', 'Message in the Telegram')
    ], ondelete={'telegram': 'set default'})
