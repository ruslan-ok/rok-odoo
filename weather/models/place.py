from odoo import models, fields


class Place(models.Model):
    _name = 'weather.place'
    _description = 'Place'

    place_id = fields.Char(required=True)
    name = fields.Char(required=True)
    adm_area1 = fields.Char()
    adm_area2 = fields.Char()
    country = fields.Char()
    lat = fields.Char()
    lon = fields.Char()
    timezone = fields.Char()
    type = fields.Char()
    search_name = fields.Char()
    lat_cut = fields.Char()
    lon_cut = fields.Char()
