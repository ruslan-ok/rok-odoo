import os
from pathlib import Path
from odoo import models, fields, _, api
from odoo.exceptions import UserError

class RokFilestoreFolder(models.TransientModel):
    _name = 'rok.filestore.folder'
    _description = 'Represent folder in filesystem'

    path = fields.Char("Filestore Path")
    name = fields.Char("Name", required=True)
    parent_id = fields.Many2one('rok.filestore.folder', "Parent Folder", ondelete='cascade', index=True)
    child_ids = fields.One2many('rok.filestore.folder', 'parent_id', "Child Folders", copy=True, auto_join=True)
    file_ids = fields.One2many('rok.filestore.file', 'folder_id', "Files", copy=True, auto_join=True)
    icon = fields.Char(string='Emoji')
    category = fields.Selection([('private', 'Private')], compute="_compute_category")
    is_locked = fields.Boolean(string='Locked',
        help="When locked, users cannot write on the body or change the title, "
             "even if they have write access on the folder.")
    is_user_favorite = fields.Boolean(
        string="Is Favorited",
        compute="_compute_is_user_favorite",
        search="_search_is_user_favorite")
    has_children = fields.Boolean('Has children folders?', compute="_compute_has_children")

    def _compute_category(self):
        for folder in self:
            folder.category = 'private'

    @api.depends_context('uid')
    def _compute_is_user_favorite(self):
        for folder in self:
            folder.is_user_favorite = False

    @api.depends('child_ids')
    def _compute_has_children(self):
        results = self.env['rok.filestore.folder']._read_group([('parent_id', 'in', self.ids)])
        count_by_folder_id = {parent.id for parent in results}
        for folder in self:
            folder.has_children = folder.id in count_by_folder_id

    @api.model
    def get_root_path(self):
        user = self.env.user
        root_path = user.filestore_path
        return root_path

    @api.model
    def get_child_folder(self, parent, name):
        parent_id = parent.id if parent else False
        child_folder = self.env["rok.filestore.folder"].search([("parent_id", "=", parent_id), ("name", "=", name)])
        if not child_folder:
            root_path = self.get_root_path()
            full_path = os.path.join(root_path, name)
            has_children = any(
                os.path.isdir(os.path.join(full_path, child))
                for child in os.listdir(full_path)
            )
            path = Path(parent.path) / name if parent else name
            child_folder = self.env["rok.filestore.folder"].create({
                "parent_id": parent_id,
                "name": name,
                "path": path,
                "icon": "📄",
                "has_children": has_children,
            })
        return child_folder
    
    def get_sidebar_folders(self, unfolded_ids=False):
        result = {
            "folders": [],
            "favorite_ids": [],
            "active_folder_accessible_root_id": False,
        }
        root_path = self.get_root_path()

        for entry in sorted(os.listdir(root_path)):
            full_path = os.path.join(root_path, entry)
            if os.path.isdir(full_path):
                folder = self.get_child_folder(False, entry)
                node = {
                    'id': folder.id,
                    'name': folder.name,
                    'parent_id': folder.parent_id.id,
                    'icon': folder.icon,
                    'category': folder.category,
                    'is_locked': folder.is_locked,
                    'user_can_write': True,
                    'is_user_favorite': folder.is_user_favorite,
                    'has_children': folder.has_children,
                }
                result["folders"].append(node)
        return result

    def _get_first_accessible_folder(self):
        folder = self.env['rok.filestore.folder']
        # if not self.env.user._is_public():
        #     folder = self.env['knowledge.folder.favorite'].search([
        #         ('user_id', '=', self.env.uid), ('is_folder_active', '=', True)
        #     ], limit=1).folder_id
        if not folder:
            # retrieve workspace folders first, then private/shared ones.
            self.get_sidebar_folders()
            folder = self.search(
                [('parent_id', '=', False)],
                limit=1,
                order='id'
            )
        return folder

    def action_home_page(self):
        folder = self[0] if self else False
        if not folder and self.env.context.get('res_id', False):
            folder = self.browse([self.env.context["res_id"]])
            if not folder.exists():
                raise UserError(_("The folder you are trying to access has been deleted"))
        if not folder:
            folder = self._get_first_accessible_folder()

        action = self.env['ir.actions.act_window']._for_xml_id('rok_filestore_qweb.rok_filestore_folder_form')
        action['res_id'] = folder.id
        return action
