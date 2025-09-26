from random import randint
from odoo import fields, models
from odoo.models import Constraint

class PasswordTag(models.Model):
    _name = "password.tag"
    _description = "Password Tag"
    _order = "sequence, id"

    def _get_default_password_id(self):
        return self.env["passwords"].browse(self.env.context.get("password_id"))

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string="Name", required=True, translate=True)
    sequence = fields.Integer(default=10)
    color = fields.Integer(string='Color', default=_get_default_color, aggregator=False)
    password_ids = fields.Many2many(
        string="Passwords",
        comodel_name="passwords",
        relation="password_tag_passwords_rel",
        default=_get_default_password_id,
    )
    active = fields.Boolean(default=True)

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        return [dict(vals, name=self.env._("%s (copy)", tag.name)) for tag, vals in zip(self, vals_list)]

    def _search_password_ids(self, operator, operand):
        return [("password_ids.product_variant_ids", operator, operand)]

    class NameUniqueConstraint(Constraint):
        _name = "name_unique"
        _model = "password.tag"
        _sql = "UNIQUE(name)"
        _message = "Tag name already exists!"
