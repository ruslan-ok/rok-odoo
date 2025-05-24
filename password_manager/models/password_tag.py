from odoo import fields, models

class PasswordTag(models.Model):
    _name = "password.tag"
    _description = "Password Tag"
    _order = "sequence, id"

    def _get_default_password_id(self):
        return self.env["passwords"].browse(self.env.context.get("password_id"))

    name = fields.Char(string="Name", required=True, translate=True)
    sequence = fields.Integer(default=10)
    color = fields.Char(string="Color", default="#3C3C3C")
    password_ids = fields.Many2many(
        string="Passwords",
        comodel_name="passwords",
        relation="password_tag_passwords_rel",
        default=_get_default_password_id,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Tag name already exists!"),
    ]

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        return [dict(vals, name=self.env._("%s (copy)", tag.name)) for tag, vals in zip(self, vals_list)]

    def _search_password_ids(self, operator, operand):
        return [("password_ids.product_variant_ids", operator, operand)]
