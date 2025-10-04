from odoo import models, api, fields, _

class RokMigrationItems(models.Model):
    _name = 'rok.migration.items'
    _description = 'Rok Migration Items'

    res_model = fields.Char(string='Res Model')
    res_id = fields.Integer(string='Res ID')
