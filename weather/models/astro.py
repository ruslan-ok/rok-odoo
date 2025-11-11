from odoo import models, fields


class Astro(models.Model):
    _name = 'weather.astro'
    _description = 'Astro'

    place_id = fields.Many2one("weather.place", required=True)
    date = fields.Date(required=True)
    day_length = fields.Integer()
    sunrise = fields.Datetime()
    sunset = fields.Datetime()
    solar_noon = fields.Datetime()
    civil_twilight_begin = fields.Datetime()
    civil_twilight_end = fields.Datetime()
    nautical_twilight_begin = fields.Datetime()
    nautical_twilight_end = fields.Datetime()
    astronomical_twilight_begin = fields.Datetime()
    astronomical_twilight_end = fields.Datetime()
