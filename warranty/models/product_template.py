from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warranty_start_date = fields.Date()
    warranty_end_date = fields.Date(compute='_compute_warranty_end_date', store=True)
    warranty_months = fields.Integer()
    warranty_is_active = fields.Boolean(compute='_compute_warranty_is_active', search='_search_warranty_is_active')

    @api.depends('warranty_start_date', 'warranty_months')
    def _compute_warranty_end_date(self):
        for product in self:
            product.warranty_end_date = (
                product.warranty_start_date
                + relativedelta(months=product.warranty_months)
                if product.warranty_start_date
                else False
            )

    @api.depends('warranty_start_date', 'warranty_end_date', 'warranty_months')
    def _compute_warranty_is_active(self):
        for product in self:
            product.warranty_is_active = (
                product.warranty_start_date <= fields.Date.today() <= product.warranty_end_date
                if product.warranty_start_date and product.warranty_months
                else False
            )

    @api.model
    def _search_warranty_is_active(self, operator, value):
        """Enable searching on non-stored boolean using other stored fields.

        We treat only boolean comparisons ("=", "!=").
        Active means: start_date <= today and months > 0 and end_date >= today.
        """
        today = fields.Date.context_today(self)
        active_domain = [
            ('warranty_start_date', '<=', today),
            ('warranty_months', '>', 0),
            ('warranty_end_date', '>=', today),
        ]

        not_active_domain = [
            '|', '|',
            ('warranty_start_date', '=', False),
            ('warranty_months', '<=', 0),
            ('warranty_end_date', '<', today),
        ]

        if operator in ('=', '=='):
            return active_domain if bool(value) else not_active_domain
        if operator == '!=':
            return not_active_domain if bool(value) else active_domain
        # Fallback: behave like '=' operator
        return active_domain if bool(value) else not_active_domain
