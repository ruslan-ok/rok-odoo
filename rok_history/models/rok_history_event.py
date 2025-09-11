from odoo import models, fields, api

class HistoryEvent(models.Model):
    _name = 'rok.history.event'
    _description = 'History Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'is_favorite desc, start_date desc'

    # The owner of the measurement; default to the current user
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        default=lambda self: self.env.user,
    )
    active = fields.Boolean(default=True)
    is_favorite = fields.Boolean(string="Favorite")
    start_date = fields.Date(compute='_compute_start_stop_dates', store=True)
    stop_date = fields.Date(compute='_compute_start_stop_dates', store=True)
    title = fields.Char()
    info = fields.Html()
    is_disease = fields.Boolean(default=False)
    diagnosis = fields.Char()
    fact_ids = fields.One2many('rok.history.fact', 'event_id')
    categ_id = fields.Many2one('rok.history.category', string='Category')

    @api.depends('fact_ids.fact_date_time')
    def _compute_start_stop_dates(self):
        for record in self:
            if record.fact_ids:
                dates = record.fact_ids.mapped('fact_date_time')
                if dates:
                    record.start_date = min(dates).date()
                    record.stop_date = max(dates).date()
                else:
                    record.start_date = False
                    record.stop_date = False
            else:
                record.start_date = False
                record.stop_date = False

    def init_by_articles(self):
        pass