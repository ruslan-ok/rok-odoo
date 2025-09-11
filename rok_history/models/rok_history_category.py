from odoo import models, fields

class HistoryCategory(models.Model):
    _name = 'rok.history.category'
    _description = 'History Category'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)