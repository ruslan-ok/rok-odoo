from odoo import models, fields, api
from odoo.addons.rok_spreadsheet.utils.delta import approximate, SourceData

class Anthropometry(models.Model):
    _name = 'rok.health.anthropometry'
    _description = 'Anthropometry'
    _order = 'measurement desc'

    # The owner of the measurement; default to the current user
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        default=lambda self: self.env.user,
    )

    # Timestamp when the measurement was taken
    measurement = fields.Datetime(
        string='Date and Time of Measurement',
        required=True,
        default=fields.Datetime.now,
    )

    height = fields.Integer(aggregator='avg')
    weight = fields.Float(aggregator='avg')
    waist = fields.Float(aggregator='avg')
    temperature = fields.Float(aggregator='avg')
    systolic = fields.Float(aggregator='avg')
    diastolic = fields.Float(aggregator='avg')
    pulse = fields.Integer(aggregator='avg')
    info = fields.Html()

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if groupby == ["measurement:day"] and fields == ["__count", "weight:avg"]:
            data = self.search(domain, offset=offset, limit=limit, order="measurement")
            src_data = [SourceData(event=x.measurement, value=x.weight) for x in data if x.measurement and x.weight]
            chart_points = approximate(src_data, 100, 'measurement:day', 'weight')
            return chart_points
        data = super(Anthropometry, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
        return data
