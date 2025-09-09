from odoo import models, fields, api

class HistoryEvent(models.Model):
    _name = 'rok.history.event'
    _description = 'History Event'
    _order = 'start_date desc'

    # The owner of the measurement; default to the current user
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        default=lambda self: self.env.user,
    )
    active = fields.Boolean(default=True)
    start_date = fields.Date(compute='_compute_start_stop_dates', store=True)
    stop_date = fields.Date(compute='_compute_start_stop_dates', store=True)
    name = fields.Char()
    info = fields.Html()
    is_disease = fields.Boolean(default=False)
    diagnosis = fields.Char()
    fact_ids = fields.One2many('rok.history.fact', 'event_id')

    @api.depends('start_date', 'stop_date')
    def _compute_start_stop_dates(self):
        for record in self:
            record.start_date = min(record.fact_ids.mapped('fact_date_time')).date() if record.fact_ids.fact_date_time else False
            record.stop_date = max(record.fact_ids.mapped('fact_date_time')).date() if record.fact_ids.fact_date_time else False

    def init_by_articles(self):
        pass