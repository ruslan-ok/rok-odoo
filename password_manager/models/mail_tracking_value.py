from odoo import api, models


class MailTracking(models.Model):
    _inherit = 'mail.tracking.value'

    @api.model
    def _create_tracking_values(self, initial_value, new_value, col_name, col_info, record):
        values = super()._create_tracking_values(initial_value, new_value, col_name, col_info, record)
        if record._name == "passwords" and col_name == "value":
            self.env["password.history"].create({
                "password_id": record.id,
                "value": values['old_value_char'],
            })
            values['new_value_char'] = '********'
            values['old_value_char'] = '********'
        return values
