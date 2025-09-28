from datetime import timedelta
from odoo import models, fields, api, fields as fields_api
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

class AnthropometryKPI(models.AbstractModel):
    _name = 'rok.health.anthropometry_kpi'
    _description = 'Anthropometry KPI'
    _order = 'current_weight desc'

    current_weight = fields.Float(aggregator='avg')
    period_start_weight = fields.Float(aggregator='avg')
    weight_change_percent = fields.Float(aggregator='avg')

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        """Override search to prevent database access."""
        if count:
            return 1
        # Return a virtual recordset with ID 1
        return self.browse([1])

    @api.model
    def read(self, ids, fields=None, load='_classic_read'):
        """Override read to provide virtual record data."""
        if isinstance(ids, int):
            ids = [ids]
        
        # Get KPI data
        domain = [('measurement', '>=', fields_api.Datetime.now() - timedelta(days=7)), ("weight", "!=", 0)]
        data = self.env['rok.health.anthropometry'].search(domain)
        current_weight = period_start_weight = weight_change_percent = 0
        if data:
            current_weight = data[0].weight
            period_start_weight = data[-1].weight
            weight_change_percent = ((current_weight - period_start_weight) / period_start_weight * 100) if period_start_weight > 0 else 0

        record = {'id': 1}
        if not fields or 'current_weight' in fields:
            record['current_weight'] = current_weight
        if not fields or 'period_start_weight' in fields:
            record['period_start_weight'] = period_start_weight
        if not fields or 'weight_change_percent' in fields:
            record['weight_change_percent'] = weight_change_percent
        
        return [record] if ids else []

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to prevent database access."""
        return [(1, 'Anthropometry KPI')]

    @api.model
    def search_count(self, domain):
        """Override search_count to prevent database access."""
        return 1

    @api.model
    def search_read(self, domain, fields, offset=0, limit=None, order=None):
        """Return KPI data as search_read format."""
        domain = [('measurement', '>=', fields_api.Datetime.now() - timedelta(days=7)), ("weight", "!=", 0)]
        data = self.env['rok.health.anthropometry'].search(domain)
        current_weight = period_start_weight = weight_change_percent = 0
        if data:
            current_weight = data[0].weight
            period_start_weight = data[-1].weight
            weight_change_percent = ((current_weight - period_start_weight) / period_start_weight * 100) if period_start_weight > 0 else 0

        # Return in search_read format with virtual ID
        record = {'id': 1}  # Virtual ID for spreadsheet compatibility

        # Only include requested fields
        if not fields or 'current_weight' in fields:
            record['current_weight'] = current_weight
        if not fields or 'period_start_weight' in fields:
            record['period_start_weight'] = period_start_weight
        if not fields or 'weight_change_percent' in fields:
            record['weight_change_percent'] = weight_change_percent
        return [record]

    @api.model
    @api.readonly
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        """Return KPI data as web_search_read format."""
        fields = list(specification.keys()) if specification else ['current_weight', 'period_start_weight', 'weight_change_percent']
        records = self.search_read(domain, fields, offset, limit, order)

        # Format for web_search_read - must return dict with 'length' and 'records'
        return {
            'length': len(records),
            'records': records
        }
