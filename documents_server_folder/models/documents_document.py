import os
import mimetypes
from collections import OrderedDict
from odoo import models, api, _, fields
from odoo.osv import expression

class Document(models.Model):
    _inherit = "documents.document"

    located_on_the_server = fields.Boolean("This object (folder or file) is located on the Server", default=False)
    has_children = fields.Boolean("Does it have child folders?", default=False)
    fetch_dt = fields.Datetime()

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        result = super().search_panel_select_range(field_name)

        if field_name == "folder_id" and not self.env.user.share:
            root_folder = self.env["documents.document"].search([
                ("type", "=", "folder"),
                ("folder_id", "=", False),
                ("located_on_the_server", "=", True),
                ("name", "=", "SERVER_FOLDER"),
                ("owner_id", "=", self.env.user.id),
                ])
            if not root_folder:
                root_folder = self.create_folder(False, "SERVER_FOLDER")
                root_folder.populate_folder("")

            enable_counters = kwargs.get("enable_counters", False)
            search_panel_fields = ["access_token", "company_id", "description", "display_name", "folder_id",
                "is_favorited", "is_pinned_folder", "owner_id", "shortcut_document_id",
                "user_permission", "active", "alias_name", "alias_domain_id", "alias_tag_ids", "partner_id",
                "create_activity_type_id", "create_activity_user_id"]
            domain = [
                ("type", "=", "folder"),
                ("located_on_the_server", "=", True),
                ("id", "!=", root_folder.id),
            ]

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

            values_range = OrderedDict()
            for record in records:
                record_id = record["id"]
                record["alias_tag_ids"] = [alias_tag_data[tag_id] for tag_id in record["alias_tag_ids"]]
                if enable_counters:
                    image_element = domain_image.get(record_id)
                    record["__count"] = image_element["__count"] if image_element else 0
                folder_id = record["folder_id"]
                record["folder_id"] = "SERVER_FOLDER" if folder_id[0] == root_folder.id else folder_id[0]
                values_range[record_id] = record

            if enable_counters:
                self._search_panel_global_counters(values_range, "folder_id")

            result["values"] += list(values_range.values())

            my_server_folder = {
                "bold": True,
                "childrenIds": [],
                "parentId": False,
                "user_permission": "edit",
                "display_name": _("Server Folder"),
                "id": "SERVER_FOLDER",
                "user_permission": "edit",
                "description": _("Your individual space on the Server."),
            }
            for i in range(len(result["values"]) - 1, -1, -1):
                if result["values"][i].get("id") == "MY":
                    result["values"].insert(i + 1, my_server_folder)
                    break
        return result

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

    def populate_folder(self, folder_path, force=False):
        self.ensure_one()
        if self.type != "folder" or not self.located_on_the_server:
            return
        if not self.root_path:
            return
        if not force and (not self.has_children or (self.fetch_dt and (fields.Datetime.now() - self.fetch_dt).days <= 5)):
            return
        children = self.env["documents.document"].with_context(active_test=False).search([("id", "child_of", self.id)])
        (children - self).unlink()
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
                folder_path = doc.get_path()
                doc.populate_folder(folder_path)
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
