from odoo import models, fields, api

class Crypto(models.TransientModel):
    _name = 'rok.crypto'
    _description = 'Crypto'

    dt = fields.Datetime(string='Datetime')
    value = fields.Float(string='Value', aggregator='avg')

    # @api.model
    # @api.readonly
    # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     print(f"read_group: {domain} {fields} {groupby} {offset} {limit} {orderby} {lazy}")
    #     rows_dict = super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
    #     return rows_dict
