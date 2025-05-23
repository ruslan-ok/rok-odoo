from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PasswordCategory(models.Model):
    _name = "password.category"
    _inherit = ["mail.thread"]
    _description = "Password Category"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "complete_name"

    name = fields.Char("Name", index="trigram", required=True)
    complete_name = fields.Char(
        "Complete Name", compute="_compute_complete_name", recursive=True,
        store=True)
    parent_id = fields.Many2one("password.category", "Parent Category", index=True, ondelete="cascade")
    parent_path = fields.Char(index=True)
    child_id = fields.One2many("password.category", "parent_id", "Child Categories")
    password_count = fields.Integer(
        "# Passwords", compute="_compute_password_count",
        help="The number of passwords under this category (Does not consider the children categories)")
    active = fields.Boolean(default=True)

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "%s / %s" % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_password_count(self):
        read_group_res = self.env["passwords"]._read_group([("categ_id", "child_of", self.ids)], ["categ_id"], ["__count"])
        group_data = {categ.id: count for categ, count in read_group_res}
        for categ in self:
            password_count = 0
            for sub_categ_id in categ.search([("id", "child_of", categ.ids)]).ids:
                password_count += group_data.get(sub_categ_id, 0)
            categ.password_count = password_count

    @api.constrains("parent_id")
    def _check_category_recursion(self):
        if self._has_cycle():
            raise ValidationError(_("You cannot create recursive categories."))

    @api.model
    def name_create(self, name):
        category = self.create({"name": name})
        return category.id, category.display_name

    @api.depends_context("hierarchical_naming")
    def _compute_display_name(self):
        if self.env.context.get("hierarchical_naming", True):
            return super()._compute_display_name()
        for record in self:
            record.display_name = record.name
