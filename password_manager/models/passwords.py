from odoo import api, fields, models, tools
from odoo.exceptions import UserError


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
    # Store encrypted value in the database
    value_encrypted = fields.Text(string="Encrypted Password", readonly=False)
    # Expose decrypted value to the UI; encrypt/decrypt transparently
    value = fields.Char(
        string="Password",
        compute="_compute_value",
        inverse="_inverse_value",
        search="_search_value",
        tracking=True,
        store=False,
    )
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

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        context = self.env.context or {}

        if "categ_id" in fields_list and not defaults.get("categ_id"):
            value = context.get("default_categ_id")
            if value is None:
                value = context.get("searchpanel_default_categ_id")

            # Accept formats used by the searchpanel: single id, list of ids, or string id
            if isinstance(value, (list, tuple)):
                value = value[0] if value else False
            if isinstance(value, str):
                # Values from the searchpanel can be stringified ids
                value = int(value) if value.isdigit() else False

            if value:
                defaults["categ_id"] = value

        return defaults

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

    # --- Encryption helpers -------------------------------------------------

    def _get_fernet(self):
        """Return a Fernet instance using a module-wide key.

        The key is stored in ir.config_parameter under 'password_manager.fernet_key'.
        """
        try:
            from cryptography.fernet import Fernet  # type: ignore
        except Exception as exc:  # pragma: no cover - dependency missing
            raise UserError(
                "Python package 'cryptography' is required for password encryption."
            ) from exc

        icp = self.env['ir.config_parameter'].sudo()
        key = icp.get_param('password_manager.fernet_key')
        if not key:
            key = Fernet.generate_key().decode()
            icp.set_param('password_manager.fernet_key', key)
        return Fernet(key.encode())

    def _encrypt_value(self, plaintext):
        if not plaintext:
            return False
        fernet = self._get_fernet()
        token = fernet.encrypt(plaintext.encode())
        return token.decode()

    def _decrypt_value(self, ciphertext):
        if not ciphertext:
            return False
        try:
            from cryptography.fernet import InvalidToken  # type: ignore
        except Exception:
            # If cryptography is missing, surface a clear error when needed
            raise UserError(
                "Python package 'cryptography' is required for password decryption."
            )
        fernet = self._get_fernet()
        try:
            value = fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            # If existing data is not decryptable (e.g., legacy plain text), just return it
            value = ciphertext
        return value

    # --- value field compute/inverse/search --------------------------------

    def _compute_value(self):
        for record in self:
            record.value = self._decrypt_value(record.value_encrypted) if record.value_encrypted else False

    def _inverse_value(self):
        for record in self:
            record.value_encrypted = self._encrypt_value(record.value) if record.value else False

    @api.model
    def _search_value(self, operator, operand):
        """Custom search over decrypted values.

        Note: This performs a python-side filter which may be slow on large datasets.
        """
        # Normalize operator handling
        op = operator or 'ilike'
        if operand is None:
            return [('id', 'in', [])]

        # Fetch candidates naively; optimize if needed later
        candidates = self.search([])
        matched_ids = []
        test_value = (operand or '')
        for rec in candidates:
            plain = rec._decrypt_value(rec.value_encrypted) if rec.value_encrypted else ''
            if op in ('ilike', 'like', '=ilike', '=like'):
                if test_value.lower() in plain.lower():
                    matched_ids.append(rec.id)
            elif op in ('=', '=='):
                if plain == operand:
                    matched_ids.append(rec.id)
            elif op in ('!=', '<>'):
                if plain != operand:
                    matched_ids.append(rec.id)
            else:
                # Fallback: do not match unknown operators
                continue
        return [('id', 'in', matched_ids)]
