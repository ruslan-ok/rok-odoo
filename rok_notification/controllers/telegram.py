import logging
import requests
from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class TelegramController(http.Controller):

    @http.route('/telegram/webhook', type='json', auth='public', csrf=False)
    def telegram_webhook(self):
        update = request.jsonrequest
        _logger.info("Telegram webhook received: %s", update)

        if "callback_query" in update:
            chat_id = update["callback_query"]["from"]["id"]
            data = update["callback_query"]["data"]

            if data == "remind_5":
                self.send_message(chat_id, "OK 👍 I will remind you in 5 minutes.")

                request.env["rok_notification.reminder"].sudo().schedule_reminder(chat_id, delay=5)

        elif "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text")

            self.send_message(chat_id, f"You wrote: {text}")

        return {"ok": True}

    def send_message(self, chat_id, text):
        if not chat_id:
            return
        TELEGRAM_TOKEN = self.env['ir.config_parameter'].sudo().get_param('rok_notification.telegram_token')
        if not TELEGRAM_TOKEN:
            raise UserError(_("Telegram token is not set"))
        TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        requests.post(TELEGRAM_API_URL, json=payload)
        _logger.info("Telegram message sent to %s: %s", chat_id, text)
