from odoo import models, fields
from ..constants import EVENT_TYPE, CURRENT


class Forecast(models.Model):
    _name = 'weather.forecast'
    _description = 'Forecast'

    place_id = fields.Many2one("weather.place", required=True)
    fixed = fields.Datetime(required=True)
    ev_type = fields.Selection(EVENT_TYPE, default=CURRENT, string='Event type: current, historical, forecasted')
    event = fields.Datetime(required=True)
    lat = fields.Char()
    lon = fields.Char()
    location = fields.Char()
    elevation = fields.Integer()
    timezone = fields.Char()
    units = fields.Char()
    weather = fields.Char()
    icon = fields.Integer()
    summary = fields.Char()
    temperature = fields.Float()
    temperature_min = fields.Float()
    temperature_max = fields.Float()
    wind_speed = fields.Float()
    wind_angle = fields.Integer()
    wind_dir = fields.Char()
    prec_total = fields.Float()
    prec_type = fields.Char()
    cloud_cover = fields.Integer()

