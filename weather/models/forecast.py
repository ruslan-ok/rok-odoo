from odoo import models, fields
from ..constants import EVENT_TYPE, CURRENT


class Forecast(models.Model):
    _name = 'weather.forecast'
    _description = 'Forecast'

    place_id = fields.Many2one("weather.place", required=True)
    fixed = fields.Datetime(required=True)
    ev_type = fields.Selection(EVENT_TYPE, default=CURRENT, string='Type')
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
    temperature = fields.Float(aggregator="avg")
    temperature_min = fields.Float(aggregator='avg')
    temperature_max = fields.Float(aggregator='avg')
    wind_speed = fields.Float(aggregator='avg')
    wind_angle = fields.Integer()
    wind_dir = fields.Char()
    prec_total = fields.Float(aggregator='avg')
    prec_type = fields.Char()
    cloud_cover = fields.Integer()

