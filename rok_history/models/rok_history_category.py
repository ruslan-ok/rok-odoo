from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HistoryCategory(models.Model):
    _name = 'rok.history.category'
    _inherit = ["mail.thread"]
    _description = 'History Category'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "complete_name"

    name = fields.Char("Name", index="trigram", required=True)
    complete_name = fields.Char(
        "Complete Name", compute="_compute_complete_name", recursive=True,
        store=True)
    parent_id = fields.Many2one("rok.history.category", "Parent Category", index=True, ondelete="cascade")
    parent_path = fields.Char(index=True)
    child_id = fields.One2many("rok.history.category", "parent_id", "Child Categories")
    categ_id = fields.Many2one(
        "rok.history.category", "History Category",
        change_default=True,
        group_expand="_read_group_categ_id",
        required=True,
    )
    event_count = fields.Integer(
        "# Events", compute="_compute_event_count",
        help="The number of events under this category (Does not consider the children categories)")
    active = fields.Boolean(default=True)

    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "%s / %s" % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_event_count(self):
        read_group_res = self.env["rok.history.event"]._read_group([("categ_id", "child_of", self.ids)], ["categ_id"], ["__count"])
        group_data = {category.id: count for category, count in read_group_res}
        for category in self:
            event_count = 0
            for sub_category_id in category.search([("id", "child_of", category.ids)]).ids:
                event_count += group_data.get(sub_category_id, 0)
            category.event_count = event_count

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

    def _read_group_categ_id(self, categories, domain):
        category_ids = self.env.context.get("default_categ_id")
        if not category_ids and self.env.context.get("group_expand"):
            category_ids = categories.sudo()._search([], order=categories._order)
        return categories.browse(category_ids)
