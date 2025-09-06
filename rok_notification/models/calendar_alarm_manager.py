from odoo import api, fields, models


class AlarmManager(models.AbstractModel):
    _inherit = 'calendar.alarm_manager'

    @api.model
    def _send_reminder(self):
        # Executed via cron
        super()._send_reminder()
        events_by_alarm = self._get_events_by_alarm_to_notify('telegram')
        if not events_by_alarm:
            return

        event_ids = list(set(event_id for event_ids in events_by_alarm.values() for event_id in event_ids))
        events = self.env['calendar.event'].browse(event_ids)
        now = fields.Datetime.now()
        attendees = events.filtered(lambda e: e.stop > now).attendee_ids.filtered(lambda a: a.state != 'declined')
        alarms = self.env['calendar.alarm'].browse(events_by_alarm.keys())
        for alarm in alarms:
            alarm_attendees = attendees.filtered(lambda attendee: attendee.event_id.id in events_by_alarm[alarm.id])
            alarm_attendees.with_context(
                calendar_template_ignore_recurrence=True,
                mail_notify_author=True,
            )._send_telegram_message_to_attendees()

        for event in events:
            if event.recurrence_id:
                next_date = event.get_next_alarm_date(events_by_alarm)
                # In cron, setup alarm only when there is a next date on the target. Otherwise the 'now()'
                # check in the call below can generate undeterministic behavior and setup random alarms.
                if next_date:
                    event.recurrence_id.with_context(date=next_date)._setup_alarms()
