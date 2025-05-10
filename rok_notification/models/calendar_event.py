import os
from dotenv import load_dotenv
from odoo import models, api
import requests


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def send_notification(self, text):
        load_dotenv()
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL") % TELEGRAM_TOKEN
        CHAT_ID = os.getenv("CHAT_ID")

        payload = {
            'chat_id': CHAT_ID,
            'text': text,
            'parse_mode': 'Markdown'
        }
        requests.post(TELEGRAM_API_URL, json=payload)
