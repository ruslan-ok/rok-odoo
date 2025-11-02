from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    birthday = fields.Date()
    age = fields.Integer(compute='_compute_age')

    def _compute_age(self):
        today = fields.Date.today()
        for record in self:
            if record.birthday:
                # Calculate age based on year difference
                age = today.year - record.birthday.year
                # Check if birthday hasn't occurred yet this year
                if today.month < record.birthday.month or (today.month == record.birthday.month and today.day < record.birthday.day):
                    age -= 1
                record.age = age
            else:
                record.age = 0