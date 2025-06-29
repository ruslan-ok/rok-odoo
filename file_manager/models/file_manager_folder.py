import os
import mimetypes
from collections import defaultdict
from pathlib import Path
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import OrderedSet

class FileManagerFolder(models.Model):
    _name = "file.manager.folder"
    _description = "Represent folder in filesystem"
    _parent_store = True

    path = fields.Char("Path to manage files")
    name = fields.Char(
        "Name", 
        required=True, 
        default="Undefined",
    )
    parent_id = fields.Many2one(
        "file.manager.folder", 
        "Parent Folder", 
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        "file.manager.folder",
        "parent_id", 
        "Child Folders", 
        copy=True, 
        auto_join=True,
    )
    file_ids = fields.One2many(
        "file.manager.file", 
        "folder_id", 
        "Files",
        copy=True, 
        auto_join=True,
    )
    icon = fields.Char(string="Emoji")
    is_user_favorite = fields.Boolean(
        string="Is Favorited",
        compute="_compute_is_user_favorite",
        search="_search_is_user_favorite",
    )
    user_favorite_sequence = fields.Integer(string="User Favorite Sequence", compute="_compute_is_user_favorite")
    favorite_ids = fields.One2many(
        "file.manager.folder.favorite", "folder_id",
        string="Favorite Folders", copy=False)
    # Set default=0 to avoid false values and messed up order
    favorite_count = fields.Integer(
        string="#Is Favorite",
        compute="_compute_favorite_count", store=True, copy=False, default=0)
    has_children = fields.Boolean(
        "Has children folders?",
    )
    children_fetched = fields.Boolean(
        "Are the child folders fetched from OS?", 
        default=False,
    )
    files_ids = fields.One2many(
        "file.manager.file", 
        "folder_id", 
        "Folder files",
    )
    # used to speed-up hierarchy operators such as child_of/parent_of
    # see "_parent_store" implementation in the ORM for details
    parent_path = fields.Char()
    root_folder_id = fields.Many2one(
        "file.manager.folder", 
        string="Menu Folder", 
        recursive=True,
        compute="_compute_root_folder_id", 
        compute_sudo=True,
        help="The subject is the title of the highest parent in the folder hierarchy.",
    )
    last_check = fields.Datetime("When this element updated last time")

    _sql_constraints = [
        ("unique_folder_path",
         "unique(path)",
         "Folder with this path is already stored.")
    ]

    @api.constrains("parent_id")
    def _check_parent_id_recursion(self):
        if self._has_cycle():
            raise ValidationError(
                _("Folders %s cannot be updated as this would create a recursive hierarchy.",
                  ", ".join(self.mapped("name"))
                 )
            )

    # ------------------------------------------------------------
    # COMPUTED FIELDS
    # ------------------------------------------------------------

    @api.depends("favorite_ids")
    def _compute_favorite_count(self):
        favorites = self.env["file.manager.folder.favorite"]._read_group(
            [("folder_id", "in", self.ids)], ["folder_id"], ["__count"]
        )
        favorites_count_by_folder = {folder.id: count for folder, count in favorites}
        for folder in self:
            folder.favorite_count = favorites_count_by_folder.get(folder.id, 0)

    @api.depends_context("uid")
    @api.depends("favorite_ids.user_id")
    def _compute_is_user_favorite(self):
        if self.env.user._is_public():
            self.is_user_favorite = False
            return
        favorites = self.env["file.manager.folder.favorite"].search([
            ("folder_id", "in", self.ids),
            ("user_id", "=", self.env.user.id),
        ])
        not_fav_folders = self - favorites.folder_id
        fav_folders = self - not_fav_folders
        fav_sequence_by_folder = {f.folder_id.id: f.sequence for f in favorites}
        if not_fav_folders:
            not_fav_folders.is_user_favorite = False
            not_fav_folders.user_favorite_sequence = -1
        if fav_folders:
            fav_folders.is_user_favorite = True
        for fav_folder in fav_folders:
            fav_folder.user_favorite_sequence = fav_sequence_by_folder[fav_folder.id]

    def _search_is_user_favorite(self, operator, value):
        if operator not in ("=", "!="):
            raise NotImplementedError("Unsupported search operation on favorite folders")

        if (value and operator == "=") or (not value and operator == "!="):
            return [("favorite_ids", "in", self.env["file.manager.folder.favorite"].sudo()._search(
                [("user_id", "=", self.env.uid)]
            ))]

        # easier than a not in on a 2many field (hint: use sudo because of
        # complicated ACL on favorite based on user access on folder)
        return [("favorite_ids", "not in", self.env["file.manager.folder.favorite"].sudo()._search(
            [("user_id", "=", self.env.uid)]
        ))]

    @api.depends("parent_id", "parent_id.root_folder_id")
    def _compute_root_folder_id(self):
        wparent = self.filtered("parent_id")
        for folder in self - wparent:
            folder.root_folder_id = folder

        if not wparent:
            return
        # group by parents to lessen number of computation
        folders_byparent = defaultdict(lambda: self.env["file.manager.folder"])
        for folder in wparent:
            folders_byparent[folder.parent_id] += folder

        for parent, folders in folders_byparent.items():
            ancestors = self.env["file.manager.folder"]
            while parent:
                if parent in ancestors:
                    raise ValidationError(
                        _("folders %s cannot be updated as this would create a recursive hierarchy.",
                          ", ".join(folders.mapped("name"))
                         )
                    )
                ancestors += parent
                parent = parent.parent_id
            folders.root_folder_id = ancestors[-1:]

    # ------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------

    @api.model
    @api.readonly
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **read_kwargs):
        if len(domain) == 1 and len(domain[0]) == 3 and domain[0][0] == "parent_id" and domain[0][1] == "=":
            folder_id = domain[0][2]
            folder = self.env["file.manager.folder"].browse(folder_id)
            self.fetch_child_folders(folder)
        return super().search_read(domain, fields, offset, limit, order, **read_kwargs)

    # ------------------------------------------------------------
    # BASE MODEL METHODS
    # ------------------------------------------------------------

    @property
    @api.model
    def root_path(self):
        return self.env.user.file_manager_path

    @api.model
    def fetch_child_folders(self, parent):
        result = self.env["file.manager.folder"]
        if not self.root_path or parent and (not parent.has_children or parent.children_fetched):
            return result
        folder_path = parent.path if parent else ""
        folder_full_path = self.root_path
        if folder_path:
            folder_full_path = os.path.join(self.root_path, folder_path)
        else:
            result = self.env["file.manager.folder"].search([("parent_id", "=", False)])
            if result:
                return result
        if not parent or os.path.isdir(folder_full_path):
            for entry_name in sorted(os.listdir(folder_full_path)):
                result |= self.fetch_folder(parent, entry_name)
        parent.children_fetched = True
        return result

    def populate_files(self):
        for folder in self:
            folder.file_ids.unlink()
            path = folder.parent_id.path if folder.parent_id else ""
            folder_full_path = os.path.join(self.root_path, path, folder.name)
            for file_name in os.listdir(folder_full_path):
                file_full_path = os.path.join(folder_full_path, file_name)
                if os.path.isfile(file_full_path):
                    file_size = os.path.getsize(file_full_path)
                    mimetype, _ = mimetypes.guess_type(file_full_path)
                    self.env["file.manager.file"].create({
                        "folder_id": folder.id,
                        "name": file_name,
                        "file_size": file_size,
                        "mimetype": mimetype or "application/octet-stream",
                    })

    @api.model
    def fetch_folder(self, parent, entry_name):
        folder = self.env["file.manager.folder"]
        path = parent.path if parent else ""
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
                "last_check": fields.Datetime.now(),
            })
            folder.populate_files()
        return folder
    
    def get_visible_folders(self, root_folders_ids, unfolded_ids):
        """ Get the folders that are visible in the sidebar with the given
        root folders and unfolded ids.

        A folder is visible if it is a root folder, or if it is a child
        folder (not item) of an unfolded visible folder.
        """
        if root_folders_ids:
            visible_folders_domain = [
            "|",
                ("id", "in", root_folders_ids),
                "&",
                    ("parent_id", "in", unfolded_ids),
                    ("id", "child_of", root_folders_ids),  # Don"t fetch hidden unfolded
            ]

            return self.env["file.manager.folder"].search(
                visible_folders_domain,
                order="id",
            )
        return self.env["file.manager.folder"]

    def get_sidebar_folders(self, unfolded_ids=False):
        """ Get the data used by the sidebar on load in the form view.
        It returns some information from every folder that is accessible by
        the user and that is either:
            - a visible root folder
            - a favorite folder (for the current user)
            - the current folder
            - an ancestor of the current folder, if the current folder is
              shown
            - a child folder of any unfolded folder that is shown
        """

        root_folder_domain = [("parent_id", "=", False)]

        # Fetch root folder_ids as sudo, ACLs will be checked on next global call fetching "all_visible_folders"
        # this helps avoiding 2 queries done for ACLs (and redundant with the global fetch)
        root_folders_ids = self.env["file.manager.folder"].sudo().search(root_folder_domain).ids

        favorite_folders_ids = self.env["file.manager.folder.favorite"].sudo().search(
            [("user_id", "=", self.env.user.id)]
        ).folder_id.ids

        # Add favorite folders and items (they are root folders in the favorite tree)
        root_folders_ids += favorite_folders_ids

        if unfolded_ids is False:
            unfolded_ids = []

        # Add active folder and its parents in list of unfolded folders
        if self.parent_id:
            unfolded_ids += self._get_ancestor_ids()
        # If the current folder is a hidden root folder, show the folder
        elif not self.parent_id and self.id:
            root_folders_ids += [self.id]

        all_visible_folders = self.get_visible_folders(root_folders_ids, unfolded_ids)

        return {
            "folders": all_visible_folders.read(
                [
                    "name",
                    "icon", 
                    "parent_id", 
                    "is_user_favorite", 
                    "has_children",
                ],
                None,  # To not fetch the name of parent_id
            ),
            "favorite_ids": favorite_folders_ids,
        }

    def _get_first_accessible_folder(self):
        folder = self.env["file.manager.folder"]
        if not self.env.user._is_public():
            folder = self.env["file.manager.folder.favorite"].search([
                ("user_id", "=", self.env.uid)
            ], limit=1).folder_id
        if not folder:
            parent = self.env["file.manager.folder"]
            folders = self.fetch_child_folders(parent)
            folder = folders[0] if folders else folder
        return folder

    def action_home_page(self):
        folder = self[0] if self else False
        if not folder and self.env.context.get("res_id", False):
            folder = self.browse([self.env.context["res_id"]])
            if not folder.exists():
                raise UserError(_("The folder you are trying to access has been deleted"))
        if not folder:
            folder = self._get_first_accessible_folder()

        action = self.env["ir.actions.act_window"]._for_xml_id("file_manager.file_manager_folder_action")
        action["res_id"] = folder.id
        return action

    def _get_ancestor_ids(self):
        """ Return the union of sets including the ids for the ancestors of
        records in recordset. E.g.,
         * if self = Folder `8` which has for parent `4` that has itself
           parent `2`, return `{2, 4}`;
         * if folder `11` is a child of `6` and is also in `self`, return
           `{2, 4, 6}`;

        :rtype: OrderedSet
        """
        ancestor_ids = OrderedSet()
        for folder in self:
            if folder.id in ancestor_ids:
                continue
            for ancestor_id in map(int, folder.parent_path.split("/")[-3::-1]):
                if ancestor_id in ancestor_ids:
                    break
                ancestor_ids.add(ancestor_id)
        return ancestor_ids

    def get_folder_hierarchy(self, exclude_folder_ids=False):
        """ Return the `display_name` values of the folders that are in the
        hierarchy (parent_path) of the given folder from the furthest ancestor to the closest one,
        excluding the ones provided in exclude_folder_ids.
        Requires a sudo to get the values of folders that are not accessible by the user (as the
        display name of the root and parent folders are shown even if the user does not have
        access to them, we consider it safe to show it for the entire hierarchy)
        """
        self.ensure_one()
        ancestor_ids = self._get_ancestor_ids()
        if exclude_folder_ids:
            ancestor_ids.difference_update(exclude_folder_ids)
        return self.sudo().browse(reversed(list(ancestor_ids))).read(["display_name"])

    def action_toggle_favorite(self):
        # need to sudo to be able to write on the folder model even with read access
        to_favorite_sudo = self.sudo().filtered(lambda folder: not folder.is_user_favorite)
        to_unfavorite = self - to_favorite_sudo
        to_favorite_sudo.write({"favorite_ids": [(0, 0, {"user_id": self.env.user.id})]})
        if to_unfavorite:
            self.env["file.manager.folder.favorite"].sudo().search([
                ("folder_id", "in", to_unfavorite.ids), ("user_id", "=", self.env.user.id)
            ]).unlink()
        # manually invalidate cache to recompute the favorites related fields
        self.invalidate_recordset(fnames=["is_user_favorite", "favorite_ids"])
        return self[0].is_user_favorite if self else False

    def web_read(self, specification: dict[str, dict]) -> list[dict]:
        self.populate_files()
        values_list = super().web_read(specification)
        return values_list
