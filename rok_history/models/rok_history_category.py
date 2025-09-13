from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class HistoryCategory(models.Model):
    _name = "rok.history.category"
    _description = "History Category"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "complete_name"

    name = fields.Char(index="trigram", required=True)
    complete_name = fields.Char(compute="_compute_complete_name", recursive=True, store=True)
    parent_id = fields.Many2one("rok.history.category", string="Parent Category", index=True, ondelete="cascade")
    parent_path = fields.Char(index=True)
    child_id = fields.One2many("rok.history.category", "parent_id", string="Child Categories")
    description = fields.Text(string="Description")
    event_count = fields.Integer(
        "# Events", compute="_compute_event_count",
        help="The number of events under this category (Does not consider the children categories)")
    active = fields.Boolean(default=True)

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "%s / %s" % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_event_count(self):
        for category in self:
            category.event_count = self.env["rok.history.event"].search_count([("categ_id", "=", category.id)])

    @api.constrains("parent_id")
    def _check_category_recursion(self):
        if self._has_cycle():
            raise ValidationError(_("You cannot create recursive categories."))

    @api.depends_context("hierarchical_naming")
    def _compute_display_name(self):
        if self.env.context.get("hierarchical_naming", True):
            return super()._compute_display_name()
        for record in self:
            record.display_name = record.name
