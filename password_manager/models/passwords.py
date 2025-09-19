from odoo import fields, models, tools


class Passwords(models.Model):
    _name = "passwords"
    _description = "Password Manager"
    _inherit = ["mail.thread"]
    _order = "is_favorite desc, title"
    _rec_name = "title"

    @tools.ormcache()
    def _get_default_login(self):
        return self.env.user.partner_id.email or self.env.user.login
    
    title = fields.Char(required=True)
    login = fields.Char(default=_get_default_login, tracking=True)
    value = fields.Char(tracking=True)
    info = fields.Html()
    categ_id = fields.Many2one(
        "password.category", "Password Category",
        change_default=True, 
        group_expand="_read_group_categ_id",
        required=True,
    )
    password_tag_ids = fields.Many2many(
        string="Tags", comodel_name="password.tag", relation="password_tag_passwords_rel"
    )
    is_favorite = fields.Boolean(string="Favorite")
    active = fields.Boolean(default=True, help="If unchecked, it will allow you to hide the password without removing it.")
    password_history_count = fields.Integer(compute='_compute_password_history_count', string='History Count')
    website = fields.Char()

    def _compute_password_history_count(self):
        for record in self:
            record.password_history_count = self.env['password.history'].search_count([('password_id', '=', record.id)])

    def action_view_password_history(self):
        self.ensure_one()
        return {
            'name': 'Password History',
            'type': 'ir.actions.act_window',
            'res_model': 'password.history',
            'view_mode': 'list,form',
            'domain': [('password_id', '=', self.id)],
            'context': {'default_password_id': self.id},
        }

    def _read_group_categ_id(self, categories, domain):
        category_ids = self.env.context.get("default_categ_id")
        if not category_ids and self.env.context.get("group_expand"):
            category_ids = categories.sudo()._search([], order=categories._order)
        return categories.browse(category_ids)
