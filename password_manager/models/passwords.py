from odoo import fields, models, tools


class Passwords(models.Model):
    _name = "passwords"
    _description = "Password Manager"
    _inherit = ["mail.thread"]
    _order = "is_favorite desc, title"

    @tools.ormcache()
    def _get_default_login(self):
        return self.env.user.work_email
    
    @tools.ormcache()
    def _get_default_category_id(self):
        return self.env.ref("passwords.password_category_all")

    title = fields.Char()
    login = fields.Char(default=_get_default_login, tracking=True)
    value = fields.Char(tracking=True)
    info = fields.Html()
    categ_id = fields.Many2one(
        "password.category", "Password Category",
        change_default=True, default=_get_default_category_id, group_expand="_read_group_categ_id",
        required=True)
    password_tag_ids = fields.Many2many(
        string="Tags", comodel_name="password.tag", relation="password_tag_passwords_rel"
    )
    is_favorite = fields.Boolean(string="Favorite")

    def _read_group_categ_id(self, categories, domain):
        category_ids = self.env.context.get("default_categ_id")
        if not category_ids and self.env.context.get("group_expand"):
            category_ids = categories.sudo()._search([], order=categories._order)
        return categories.browse(category_ids)
