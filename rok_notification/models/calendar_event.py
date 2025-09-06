from odoo import models, fields


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def _get_trigger_alarm_types(self):
        return super()._get_trigger_alarm_types() + ['telegram']

    def get_telegram_time_text(self, tz=False):
        self.ensure_one()
        if not self.start:
            return ""
        ctx_model = self.with_context(tz=tz) if tz else self
        local_dt = fields.Datetime.context_timestamp(ctx_model, fields.Datetime.from_string(self.start))
        today_local = fields.Date.context_today(ctx_model)
        if local_dt.date() == today_local:
            return f"at {local_dt.strftime('%H:%M')}"
        return f"{local_dt.strftime('%Y-%m-%d')} at {local_dt.strftime('%H:%M')}"
