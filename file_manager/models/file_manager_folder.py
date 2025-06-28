import os
import mimetypes
from pathlib import Path
from odoo import models, fields, _, api
from odoo.exceptions import UserError

class FileManagerFolder(models.TransientModel):
    _name = 'file.manager.folder'
    _description = 'Represent folder in filesystem'

    path = fields.Char("Path to manage files")
    name = fields.Char("Name", required=True, default="Undefined")
    parent_id = fields.Many2one('file.manager.folder', "Parent Folder", ondelete='cascade', index=True)
    child_ids = fields.One2many('file.manager.folder', 'parent_id', "Child Folders", copy=True, auto_join=True)
    file_ids = fields.One2many('file.manager.file', 'folder_id', "Files", copy=True, auto_join=True)
    icon = fields.Char(string='Emoji')
    category = fields.Selection([('private', 'Private')], compute="_compute_category")
    is_locked = fields.Boolean(string='Locked',
        help="When locked, users cannot write on the body or change the title, "
             "even if they have write access on the folder.")
    is_user_favorite = fields.Boolean(
        string="Is Favorited",
        compute="_compute_is_user_favorite",
        search="_search_is_user_favorite")
    has_children = fields.Boolean('Has children folders?')
    children_fetched = fields.Boolean('Are the child folders fetched from OS?', default=False)
    files_ids = fields.One2many("file.manager.file", "folder_id", "Folder files")

    def _compute_category(self):
        for folder in self:
            folder.category = 'private'

    @api.depends_context('uid')
    def _compute_is_user_favorite(self):
        for folder in self:
            folder.is_user_favorite = False

    @api.model
    @api.readonly
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **read_kwargs):
        if len(domain) == 1 and len(domain[0]) == 3 and domain[0][0] == "parent_id" and domain[0][1] == "=":
            folder_id = domain[0][2]
            folder = self.env["file.manager.folder"].browse(folder_id)
            self.fetch_child_folders(folder)
        return super().search_read(domain, fields, offset, limit, order, **read_kwargs)

    @property
    @api.model
    def root_path(self):
        return self.env.user.file_manager_path

    @api.model
    def fetch_child_folders(self, parent):
        result = self.env["file.manager.folder"]
        if not self.root_path or parent and (not parent.has_children or parent.children_fetched):
            return result
        folder_path = parent.path if parent else ''
        folder_full_path = self.root_path
        if folder_path:
            folder_full_path = os.path.join(self.root_path, folder_path)
        if not parent or os.path.isdir(folder_full_path):
            for entry_name in sorted(os.listdir(folder_full_path)):
                result |= self.fetch_folder(parent, entry_name)
        parent.children_fetched = True
        return result

    @api.model
    def fetch_folder(self, parent, entry_name):
        folder = self.env["file.manager.folder"]
        path = parent.path if parent else ''
        entry_full_path = os.path.join(self.root_path, path, entry_name)
        if os.path.isdir(entry_full_path):
            has_children = any(
                os.path.isdir(os.path.join(entry_full_path, child))
                for child in os.listdir(entry_full_path)
            )
            path_obj = Path(path) / entry_name
            folder = self.env["file.manager.folder"].create({
                "parent_id": parent.id if parent else False,
                "name": entry_name,
                "path": str(path_obj),
                "icon": "📂",
                "has_children": has_children,
                "children_fetched": False,
            })
            for file_name in os.listdir(entry_full_path):
                file_full_path = os.path.join(entry_full_path, file_name)
                if os.path.isfile(file_full_path):
                    file_size = os.path.getsize(file_full_path)
                    mime_type, _ = mimetypes.guess_type(file_full_path)
                    self.env["file.manager.file"].create({
                        "folder_id": folder.id,
                        "name": file_name,
                        "file_size": file_size,
                        "mime_type": mime_type or "application/octet-stream",
                    })
        return folder
    
    def get_sidebar_folders(self, unfolded_ids=False):
        result = {
            "folders": [],
            "favorite_ids": [],
            "active_folder_accessible_root_id": False,
        }
        parent = self.env["file.manager.folder"]
        child_folders = self.fetch_child_folders(parent)
        for folder in child_folders:
            node = {
                'id': folder.id,
                'name': folder.name,
                'parent_id': folder.parent_id.id,
                'icon': folder.icon,
                'category': folder.category,
                'is_locked': folder.is_locked,
                'is_user_favorite': folder.is_user_favorite,
                'has_children': folder.has_children,
            }
            result["folders"].append(node)
        return result

    def _get_first_accessible_folder(self):
        folder = self.env['file.manager.folder']
        # if not self.env.user._is_public():
        #     folder = self.env['knowledge.folder.favorite'].search([
        #         ('user_id', '=', self.env.uid), ('is_folder_active', '=', True)
        #     ], limit=1).folder_id
        if not folder:
            parent = self.env["file.manager.folder"]
            folders = self.fetch_child_folders(parent)
            folder = folders[0] if folders else folder
        return folder

    def action_home_page(self):
        folder = self[0] if self else False
        if not folder and self.env.context.get('res_id', False):
            folder = self.browse([self.env.context["res_id"]])
            if not folder.exists():
                raise UserError(_("The folder you are trying to access has been deleted"))
        if not folder:
            folder = self._get_first_accessible_folder()

        action = self.env['ir.actions.act_window']._for_xml_id('file_manager.file_manager_folder_action')
        action['res_id'] = folder.id
        return action
