import base64
import os
import shutil
import mimetypes
from collections import OrderedDict
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import image_process
from odoo.addons.documents.models.documents_document import Document as Document_for_patching


class Document(models.Model):
    _inherit = "documents.document"

    located_on_the_server = fields.Boolean("This object (folder or file) is located on the Server", default=False)
    has_children = fields.Boolean("Does it have child folders?", default=False)
    fetch_dt = fields.Datetime()

    def _register_hook(self):
        super()._register_hook()

        @api.model
        def search_panel_select_range_patch(self, field_name, **kwargs):
            return self.search_panel_select_range_patched(field_name, **kwargs)

        Document_for_patching.search_panel_select_range = search_panel_select_range_patch

    @api.model
    def search_panel_select_range_patched(self, field_name, **kwargs):
        if field_name == "folder_id":
            enable_counters = kwargs.get("enable_counters", False)
            search_panel_fields = ["access_token", "company_id", "description", "display_name", "folder_id",
                                    "is_favorited", "is_pinned_folder", "owner_id", "shortcut_document_id",
                                    "user_permission", "active"]
            if not self.env.user.share:
                search_panel_fields += ["alias_name", "alias_domain_id", "alias_tag_ids", "partner_id",
                                        "create_activity_type_id", "create_activity_user_id", "located_on_the_server"]
            domain = [
                ("type", "=", "folder"),
                '|',
                ('located_on_the_server', '=', False),
                ('owner_id', '=', self.env.user.id)]

            if unique_folder_id := self.env.context.get("documents_unique_folder_id"):
                values = self.env["documents.document"].search_read(
                    expression.AND([domain, [("folder_id", "child_of", unique_folder_id)]]),
                    search_panel_fields,
                    order="name asc",
                )
                accessible_folder_ids = {rec["id"] for rec in values}
                for record in values:
                    if folder_id := record["folder_id"]:
                        record["folder_id"] = folder_id[0] if folder_id[0] in accessible_folder_ids else False
                return {
                    "parent_field": "folder_id",
                    "values": values,
                }

            records = self.env["documents.document"].search_read(domain, search_panel_fields, order="name asc")
            accessible_folder_ids = {rec["id"] for rec in records}
            alias_tag_data = {}
            if not self.env.user.share:
                alias_tag_ids = {alias_tag_id for rec in records for alias_tag_id in rec["alias_tag_ids"]}
                alias_tag_data = {
                    alias_tag["id"]: {
                        "id": alias_tag.id,
                        "color": alias_tag.color,
                        "display_name": alias_tag.display_name
                    } for alias_tag in self.env["documents.tag"].browse(alias_tag_ids)
                }
            domain_image = {}
            if enable_counters:
                model_domain = expression.AND([
                    kwargs.get("search_domain", []),
                    kwargs.get("category_domain", []),
                    kwargs.get("filter_domain", []),
                    [(field_name, "!=", False)]
                ])
                domain_image = self._search_panel_domain_image(field_name, model_domain, enable_counters)

            # Read the targets in batch
            targets = self.browse(r["shortcut_document_id"][0] for r in records if r["shortcut_document_id"])
            targets_user_permission = {t.id: t.user_permission for t in targets}

            values_range = OrderedDict()
            shared_root_id = "SHARED" if not self.env.user.share else False
            server_folder = self.env["documents.document"].search(
                [
                    ("located_on_the_server", "=", True),
                    ("folder_id", "=", False),
                    ("name", "=", "SERVER_FOLDER"),
                ]
            )
            if not server_folder:
                server_folder = self.create_folder(False, "SERVER_FOLDER")
            for record in records:
                record_id = record["id"]
                if not self.env.user.share:
                    record["alias_tag_ids"] = [alias_tag_data[tag_id] for tag_id in record["alias_tag_ids"]]
                if enable_counters:
                    image_element = domain_image.get(record_id)
                    record["__count"] = image_element["__count"] if image_element else 0
                if record["shortcut_document_id"]:
                    record["target_user_permission"] = targets_user_permission[record["shortcut_document_id"][0]]
                folder_id = record["folder_id"]
                if folder_id:
                    folder_id = folder_id[0]
                    if folder_id not in accessible_folder_ids:
                        if record["shortcut_document_id"]:
                            continue
                        folder_id = shared_root_id
                    if folder_id == server_folder.id:
                        folder_id = "SERVER_FOLDER"
                elif record["owner_id"][0] == self.env.user.id:
                    if record["located_on_the_server"]:
                        continue
                    else:
                        folder_id = "MY"
                elif record["owner_id"][0] != self.env.ref("base.user_root").id or self.env.user.share:
                    if record["shortcut_document_id"]:
                        continue
                    folder_id = shared_root_id
                else:
                    folder_id = "COMPANY"

                record["folder_id"] = folder_id
                values_range[record_id] = record

            if enable_counters:
                self._search_panel_global_counters(values_range, "folder_id")

            special_roots = []
            if not self.env.user.share:
                special_roots = [
                    {"bold": True, "childrenIds": [], "parentId": False, "user_permission": "edit"} | values
                    for values in [
                        {
                            "display_name": _("Company"),
                            "id": "COMPANY",
                            "description": _("Common roots for all company users."),
                            "user_permission": "view",
                        }, {
                            "display_name": _("My Drive"),
                            "id": "MY",
                            "user_permission": "edit",
                            "description": _("Your individual space."),
                        }, {
                            "display_name": _("Server Folder"),
                            "id": "SERVER_FOLDER",
                            "user_permission": "edit",
                            "description": _("Your individual server space."),
                        }, {
                            "display_name": _("Shared with me"),
                            "id": "SHARED",
                            "description": _("Additional documents you have access to."),
                        }, {
                            "display_name": _("Recent"),
                            "id": "RECENT",
                            "description": _("Recently accessed documents."),
                        }, {
                            "display_name": _("Trash"),
                            "id": "TRASH",
                            "description": _("Items in trash will be deleted forever after %s days.",
                                self.get_deletion_delay()),
                        }]
                ]

            return {
                "parent_field": "folder_id",
                "values": list(values_range.values()) + special_roots,
            }

        return super().search_panel_select_range(field_name)

    @property
    @api.model
    def root_path(self):
        return self.env.user.server_folder_path

    @api.model
    def check_has_children(self, path=""):
        entry_full_path = os.path.join(self.root_path, path)
        if os.path.isdir(entry_full_path):
            has_children = any(
                os.path.isdir(os.path.join(entry_full_path, child))
                for child in os.listdir(entry_full_path)
            )
            return has_children
        return False

    @api.model
    def create_folder(self, folder_id, folder_name):
        return self.env["documents.document"].create({
            "type": "folder",
            "located_on_the_server": True,
            "folder_id": folder_id,
            "name": folder_name,
            "owner_id": self.env.user.id,
            "has_children": self.check_has_children(""),
        })

    @api.model
    def create_file(self, folder_id, folder_full_path, file_name):
        file_full_path = os.path.join(folder_full_path, file_name)
        file_size = os.path.getsize(file_full_path)
        mimetype, _ = mimetypes.guess_type(file_full_path)
        return self.env["documents.document"].create({
            "type": "binary",
            "located_on_the_server": True,
            "folder_id": folder_id,
            "name": file_name,
            "owner_id": self.env.user.id,
            "file_size": file_size,
            "mimetype": mimetype or "application/octet-stream",
        })

    def populate_folder(self):
        self.ensure_one()
        if self.type != "folder" or not self.located_on_the_server:
            return
        if not self.root_path:
            return
        if self.name == "SERVER_FOLDER":
            self.has_children = self.check_has_children()
        if not self.has_children or self.fetch_dt:
            return
        children = self.env["documents.document"].with_context(active_test=False).search([("id", "child_of", self.id)])
        (children - self).unlink()
        folder_path = self.get_path()
        folder_full_path = os.path.join(self.root_path, folder_path)
        if os.path.isdir(folder_full_path):
            for child in os.listdir(folder_full_path):
                if os.path.isdir(os.path.join(folder_full_path, child)):
                    self.create_folder(self.id, child)
                elif os.path.isfile(os.path.join(folder_full_path, child)):
                    self.create_file(self.id, folder_full_path, child)
        self.fetch_dt = fields.Datetime.now()

    @api.model
    @api.readonly
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        if len(domain) == 1 and len(domain[0]) == 3 and domain[0][0] == "folder_id":
            folder_id = domain[0][2]
            if isinstance(folder_id, str):
                doc = self.env["documents.document"].search([("name", "=", folder_id)])
            elif isinstance(folder_id, int):
                doc = self.env["documents.document"].search([("id", "=", folder_id)])
            if doc.type == "folder" and doc.located_on_the_server:
                doc.populate_folder()
                domain += [('owner_id', '=', self.env.user.id)]
        if (len(domain) == 3 and len(domain[0]) == 1 and domain[0] == "&" and len(domain[1]) == 3 and domain[1][0] == "folder_id" and
            domain[1][1] == "=" and len(domain[2]) == 3 and domain[2][0] == "owner_id" and domain[2][1] == "="):
            filter = ["located_on_the_server", "=", False]
            domain.append(filter)
        records = super().web_search_read(domain, specification, offset, limit, order, count_limit)
        return records

    def get_path(self):
        self.ensure_one()
        names = []
        parent_path_list = self.parent_path.split("/")[1:-1]
        for folder_id in parent_path_list:
            doc = self.env["documents.document"].browse(int(folder_id))
            names.append(doc.name)
        return "/".join(names)

    def get_full_path(self, check_exist=True):
        self.ensure_one()
        if not self.located_on_the_server:
            return None
        path = self.get_path()
        full_path = os.path.join(self.root_path, path)
        is_abs = os.path.isabs(full_path)
        if not is_abs:
            raise FileNotFoundError("File not found: " + full_path)
        full_path = os.path.normpath(os.path.normcase(full_path))
        if self.active and not os.path.exists(full_path):
            if check_exist:
                raise FileNotFoundError("File not found: " + full_path)
            return None
        return full_path

    @api.model_create_multi
    def create(self, vals_list):
        folder_id = self.env.context.get("default_folder_id")
        folder = self.env["documents.document"].browse(folder_id)
        if folder.located_on_the_server:
            self = self.with_context(default_located_on_the_server=True)
        documents = super().create(vals_list)
        if folder.located_on_the_server:
            for vals in vals_list:
                if vals["type"] == "folder":
                    folder_name = vals["name"]
                    folder_path = folder.get_full_path()
                    path = os.path.join(folder_path, folder_name)
                    if not os.path.exists(path):
                        os.makedirs(path)
        return documents

    def write(self, vals):
        name = vals.get("name")
        if name and self.located_on_the_server:
            old_path = self.get_full_path()
            folder_path = os.path.dirname(old_path)
            new_path = os.path.join(folder_path, name)
            if old_path != new_path:
                os.rename(old_path, new_path)
        return super().write(vals)

    def toggle_active(self):
        server_items = self.filtered("located_on_the_server")
        active_items = server_items.filtered(self._active_name)
        for item in active_items:
            path = item.get_full_path(check_exist=False)
            if path:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        inactive_items = self - active_items
        folders_to_restore = inactive_items.filtered(lambda x: x.type == "folder")
        for folder in folders_to_restore:
            path = folder.get_full_path()
            os.makedirs(path)
        super().toggle_active()

    def copy(self, default=None):
        server_items = self.filtered("located_on_the_server")
        server_files = server_items.filtered(lambda x: x.type != "folder")
        for file in server_files:
            old_path = file.get_full_path()
            new_path = old_path + " (copy)"
            shutil.copyfile(old_path, new_path)
        return super().copy(default)

    @api.depends("checksum", "shortcut_document_id.thumbnail", "shortcut_document_id.thumbnail_status", "shortcut_document_id.user_permission")
    def _compute_thumbnail(self):
        for document in self:
            if document.shortcut_document_id:
                if document.shortcut_document_id.user_permission != "none":
                    document.thumbnail = document.shortcut_document_id.thumbnail
                    document.thumbnail_status = document.shortcut_document_id.thumbnail_status
                else:
                    document.thumbnail = False
                    document.thumbnail_status = "restricted"
            elif document.mimetype and document.mimetype.startswith("application/pdf"):
                # Thumbnails of pdfs are generated by the client. To force the generation, we invalidate the thumbnail.
                document.thumbnail = False
                document.thumbnail_status = "client_generated"
            elif document.mimetype and document.mimetype.startswith("image/"):
                try:
                    document.thumbnail = base64.b64encode(image_process(document.get_raw(), size=(200, 140), crop="center"))
                    document.thumbnail_status = "present"
                except (UserError, TypeError):
                    document.thumbnail = False
                    document.thumbnail_status = "error"
            else:
                document.thumbnail = False
                document.thumbnail_status = False

    def get_raw(self):
        self.ensure_one()
        if not self.located_on_the_server:
            return self.raw
        path = self.get_full_path()
        with open(path, "rb") as file:
            return file.read()

    def _get_is_multipage(self):
        if self.located_on_the_server:
            return None
        return super()._get_is_multipage()

    def _exist_on_the_server(self):
        try:
            self.get_full_path()
            return True
        except FileNotFoundError:
            return False

    def refresh_server_folder(self):
        self.ensure_one()
        items_to_unlink = self.env["documents.document"]

        child_folders = self.children_ids.filtered(lambda x: x.type =="folder")
        for folder in child_folders:
            folder.refresh_server_folder()

        child_files = self.children_ids - child_folders
        for file in child_files:
            if file.type == "binary" and not file._exist_on_the_server():
                items_to_unlink += file

        items_to_unlink.unlink()
        if not self.children_ids and not self._exist_on_the_server():
            self.unlink()
        else:
            self.fetch_dt = False

        return {"type": "ir.actions.client", "tag": "reload"}