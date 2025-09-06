import requests

from odoo import models, _
from odoo.exceptions import UserError


class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    def _send_telegram_message_to_attendees(self):
        if self.env['ir.config_parameter'].sudo().get_param('calendar.block_telegram') or self._context.get("no_telegram_to_attendees"):
            return False

        notified_attendees_ids = set(self.ids)
        for event, attendees in self.grouped('event_id').items():
            if event._skip_send_mail_status_update():
                notified_attendees_ids -= set(attendees.ids)
        notified_attendees = self.browse(notified_attendees_ids)

        for attendee in notified_attendees:
            if attendee.partner_id.telegram_chat_id and attendee._should_notify_attendee():
                tz = attendee.partner_id.tz or False
                when_text = attendee.event_id.get_telegram_time_text(tz=tz)
                message = f"{attendee.event_id.name}\n{when_text}"
                attendee.send_notification(message)

    def send_notification(self, message):
        self.ensure_one()
        if not self.partner_id.telegram_chat_id:
            return
        TELEGRAM_TOKEN = self.env['ir.config_parameter'].sudo().get_param('rok_notification.telegram_token')
        if not TELEGRAM_TOKEN:
            raise UserError(_("Telegram token is not set"))
        TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        payload = {
            'chat_id': self.partner_id.telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        requests.post(TELEGRAM_API_URL, json=payload)

