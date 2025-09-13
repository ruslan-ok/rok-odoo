from odoo import models, fields

class HistoryFact(models.Model):
    _name = 'rok.history.fact'
    _description = 'History Fact'
    _order = 'fact_date_time desc'

    event_id = fields.Many2one('rok.history.event')
    user_id = fields.Many2one(related='event_id.user_id')
    fact_date_time = fields.Datetime(required=True, default=fields.Datetime.now)
    fact = fields.Char()
    info = fields.Html()
    is_disease = fields.Boolean(related='event_id.is_disease')
    temperature = fields.Float()