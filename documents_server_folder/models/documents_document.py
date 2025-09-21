import base64
import io
import os
import shutil
import mimetypes
import zipfile
from collections import OrderedDict
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tools.image import image_process
from odoo.addons.web.models.models import Base as BaseDocument
from odoo.addons.documents.models.documents_document import DocumentsDocument as Document_for_patching
from odoo.addons.documents_spreadsheet.models.documents_document import SUPPORTED_PATHS, XLSX_MIME_TYPES


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    located_on_the_server = fields.Boolean("This object (folder or file) is located on the Server", default=False)

    def _register_hook(self):
        super()._register_hook()

        @api.model
        def search_panel_select_range_patch(self, field_name, **kwargs):
            return self.search_panel_select_range_patched(field_name, **kwargs)

        Document_for_patching.search_panel_select_range_origin = Document_for_patching.search_panel_select_range
        Document_for_patching.search_panel_select_range = search_panel_select_range_patch

    def _unregister_hook(self):
        super()._unregister_hook()
        Document_for_patching.search_panel_select_range = Document_for_patching.search_panel_select_range_origin
        Document_for_patching.search_panel_select_range_origin = None

    @api.depends_context('uid')
    @api.depends('folder_id', 'folder_id.user_permission', 'owner_id', 'active')
    def _compute_user_folder_id(self):
        SHARED = 'SHARED' if not self.env.user.share else False
        self.user_folder_id = False  # Inaccessible
        active_documents = self.filtered('active')
        (self - active_documents).user_folder_id = "TRASH"
        for document in active_documents.filtered(lambda d: d.user_permission != 'none'):
            if document.folder_id:
                if document.folder_id.user_permission != 'none':
                    document.user_folder_id = str(document.folder_id.id)
                else:
                    document.user_folder_id = SHARED
            elif self.env.user.share:
                document.user_folder_id = False
            elif not document.owner_id:
                document.user_folder_id = 'COMPANY'
            elif document.owner_id == self.env.user:
                if document.located_on_the_server:
                    document.user_folder_id = 'SERVER_FOLDER'  # Root of user's server space
                else:
                    document.user_folder_id = 'MY'  # Root of user's drive
            else:
                document.user_folder_id = SHARED  # Root of another user's drive

    def _search_user_folder_id(self, operator, operand):
        """Search domain for user_folder_id virtual folder_id.

        Note that searching in "RECENT" is allowed for practicality w.r.t. webclient
        even though no record will have "RECENT" as computed `user_folder_id`
        """
        if operator not in ('in', 'child_of'):
            return NotImplemented
        values = {operand} if isinstance(operand, str) else set(operand)
        if 'TRASH' in values:
            # Would need `active_test=False` in context
            raise UserError(_("Searching on TRASH is not supported."))
        domain_parts = []
        folder_ids = []
        for value in values:
            if isinstance(value, int):
                value = str(value)
            elif not isinstance(value, str):
                raise UserError(_("Invalid search operand."))
            if not value and self.env.user.share:
                domain_parts.append(Domain("folder_id", "=", False) | Domain('folder_id', 'not any', []))
            elif not value:
                domain_parts.append(Domain.FALSE)
            elif value == "COMPANY":
                domain_parts.append(Domain('folder_id', '=', False) & Domain('owner_id', '=', False) & Domain('located_on_the_server', '=', False))
            elif value == "MY":
                domain_parts.append(Domain('folder_id', '=', False) & Domain('owner_id', '=', self.env.user.id) & Domain('located_on_the_server', '=', False))
            elif value == "SERVER_FOLDER":
                domain_parts.append(Domain('located_on_the_server', '=', True))
            elif value == "RECENT":
                domain_parts.append(Domain(
                    'access_ids', 'any',
                    Domain('partner_id', '=', self.env.user.partner_id.id) & Domain('last_access_date', '!=', False)))
            elif value == "SHARED":
                # Find records without permission on folder_id as directly searching on user_permission = 'none' is not allowed.
                domain_parts.append(
                    Domain('folder_id', '!=', False) & Domain('folder_id', 'not any', [])
                    | Domain("folder_id", "=", False) & Domain("owner_id", "not in", [self.env.user.id, False])
                )
            elif value.isnumeric():
                folder_ids.append(int(value))
            else:
                raise UserError(_("Unknown searched value %s", value))

        if folder_ids:
            domain_parts.append(Domain('folder_id', 'in', folder_ids))

        domain = Domain.OR(domain_parts)

        if operator == 'child_of':
            # as ('id', 'child_of', domain') doesn't work, and for performance reasons.
            # (rules will be applied on final domain)
            top_level = self.with_context(active_test=False).sudo().search_fetch(domain, ['type'])
            top_level_folders = top_level.filtered(lambda d: d.type == 'folder')
            return Domain('id', 'in', top_level.ids) | Domain('folder_id', 'child_of', top_level_folders.ids)
        return domain

    @api.model
    def _clean_vals_for_user_folder_id(self, vals):
        user_folder_id = vals.get('user_folder_id')
        if not user_folder_id:
            if (
                (default_user_folder_id := self.env.context.get('default_user_folder_id'))
                and 'folder_id' not in vals
                and 'owner_id' not in vals
                and 'default_folder_id' not in self.env.context
                and 'default_owner_id' not in self.env.context
            ):
                user_folder_id = default_user_folder_id
            else:
                return

        if user_folder_id == "SERVER_FOLDER":
            new_vals = {'located_on_the_server': True, 'owner_id': False, 'folder_id': False}
            vals.update(new_vals)
        super()._clean_vals_for_user_folder_id(vals)

    def _get_search_panel_fields(self):
        """Return the list of fields used by the search panel."""
        search_panel_fields = super()._get_search_panel_fields()
        if not self.env.user.share:
            search_panel_fields += ['located_on_the_server']
        return search_panel_fields

    @api.model
    def search_panel_select_range_patched(self, field_name, **kwargs):
        def convert_user_folder_ids_to_int(vals):
            """Convert user_folder_id to int where applicable to construct categoryTree matching on id of parent."""
            if (user_folder_id := vals['user_folder_id']) and user_folder_id.isnumeric():
                vals['user_folder_id'] = int(user_folder_id)

        if field_name == 'user_folder_id':
            if self.root_path:
                domain = Domain('type', '=', 'folder') & Domain('located_on_the_server', '=', True) & Domain('owner_id', '=', self.env.user.id)
                records_count = self.env['documents.document'].search_count(domain)
                if not records_count:
                    self.populate_folder(recursive=True)

            enable_counters = kwargs.get('enable_counters', False)
            search_panel_fields = self._get_search_panel_fields()
            domain = Domain('type', '=', 'folder') & Domain('located_on_the_server', '=', False)
            if self.root_path:
                domain = Domain.OR([domain, Domain('type', '=', 'folder') & Domain('located_on_the_server', '=', True) & Domain('owner_id', '=', self.env.user.id)])

            if unique_folder_id := self.env.context.get('documents_unique_folder_id'):
                values = self.env['documents.document'].search_read(
                    domain & Domain('folder_id', 'child_of', unique_folder_id),
                    search_panel_fields,
                )
                map(convert_user_folder_ids_to_int, values)
                for record in values:
                    if record['id'] == unique_folder_id:
                        record['user_folder_id'] = False  # Set as root
                        break
                return {
                    'parent_field': 'user_folder_id',
                    'values': values,
                }

            records = self.env['documents.document'].search_read(domain, search_panel_fields)
            alias_tag_data = {}
            if not self.env.user.share:
                alias_tag_ids = {alias_tag_id for rec in records for alias_tag_id in rec['alias_tag_ids']}
                alias_tag_data = {
                    alias_tag['id']: {
                        'id': alias_tag.id,
                        'color': alias_tag.color,
                        'display_name': alias_tag.display_name
                    } for alias_tag in self.env['documents.tag'].browse(alias_tag_ids)
                }
            domain_image = {}
            if enable_counters:
                model_domain = Domain.AND([
                    kwargs.get('search_domain', []),
                    kwargs.get('category_domain', []),
                    kwargs.get('filter_domain', []),
                    Domain(field_name, '!=', False),
                ])
                domain_image = self._search_panel_domain_image(field_name, model_domain, enable_counters)

            # Read the targets in batch
            targets = self.browse(r['shortcut_document_id'][0] for r in records if r['shortcut_document_id'])
            targets_user_permission = {t.id: t.user_permission for t in targets}

            values_range = OrderedDict()
            for record in records:
                record_id = record['id']
                convert_user_folder_ids_to_int(record)
                if not self.env.user.share:
                    record['alias_tag_ids'] = [alias_tag_data[tag_id] for tag_id in record['alias_tag_ids']]
                if enable_counters:
                    image_element = domain_image.get(record_id)
                    record['__count'] = image_element['__count'] if image_element else 0
                if record['shortcut_document_id']:
                    record['target_user_permission'] = targets_user_permission[record['shortcut_document_id'][0]]
                values_range[record_id] = record

            if enable_counters:
                self._search_panel_global_counters(values_range, 'user_folder_id')

            special_roots = []
            if not self.env.user.share:
                special_roots = [
                    {'bold': True, 'childrenIds': [], 'parentId': False, 'user_permission': 'edit'} | values
                    for values in [
                        {
                            'display_name': _("Company"),
                            'id': 'COMPANY',
                            'description': _("Common roots for all company users."),
                            'user_permission': 'edit' if self.env.user.has_group('documents.group_documents_manager') else 'view',
                        }, {
                            'display_name': _("My Drive"),
                            'id': 'MY',
                            'user_permission': 'edit',
                            'description': _("Your individual space."),
                        }, {
                            "display_name": _("Server Folder"),
                            "id": "SERVER_FOLDER",
                            "user_permission": "edit",
                            "description": _("Your individual server space."),
                        }, {
                            'display_name': _("Shared with me"),
                            'id': 'SHARED',
                            'description': _("Additional documents you have access to."),
                        }, {
                            'display_name': _("Recent"),
                            'id': 'RECENT',
                            'description': _("Recently accessed documents."),
                        }] if values["id"] != "SERVER_FOLDER" or self.root_path
                    ]
                if not self.env.context.get('documents_search_panel_no_trash'):
                    special_roots.append({
                        'display_name': _("Trash"),
                        'id': 'TRASH',
                        'description': _("Items in trash will be deleted forever after %s days.",
                                            self.get_deletion_delay()),
                    })

            return {
                'parent_field': 'user_folder_id',
                'values': list(values_range.values()) + special_roots,
            }

        return BaseDocument.search_panel_select_range(self, field_name, **kwargs)

    @property
    @api.model
    def root_path(self):
        return self.env.user.server_folder_path

    @api.model
    def check_has_children(self, path=""):
        if not self.root_path:
            return False
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
        folder = self.env["documents.document"].search([
            ("type", "=", "folder"),
            ("located_on_the_server", "=", True),
            ("folder_id", "=", folder_id),
            ("name", "=", folder_name),
            ("owner_id", "=", self.env.user.id),
        ])
        if folder:
            return folder
        return self.env["documents.document"].create({
            "type": "folder",
            "located_on_the_server": True,
            "folder_id": folder_id,
            "name": folder_name,
            "owner_id": self.env.user.id,
        })

    @api.model
    def create_file(self, folder_id, folder_full_path, file_name):
        file_full_path = os.path.join(folder_full_path, file_name)
        file_size = os.path.getsize(file_full_path)
        mimetype, _ = mimetypes.guess_type(file_full_path)
        file = self.env["documents.document"].search([
            ("type", "=", "binary"),
            ("located_on_the_server", "=", True),
            ("folder_id", "=", folder_id),
            ("name", "=", file_name),
            ("owner_id", "=", self.env.user.id),
        ])
        if file:
            return file
        return self.env["documents.document"].create({
            "type": "binary",
            "located_on_the_server": True,
            "folder_id": folder_id,
            "name": file_name,
            "owner_id": self.env.user.id,
            "file_size": file_size,
            "mimetype": mimetype or "application/octet-stream",
        })

    @api.model
    def populate_folder(self, parent_folder=False, recursive=False):
        if not self.root_path:
            return
        if parent_folder and (parent_folder.type != "folder" or not parent_folder.located_on_the_server):
            return
        parent_id = False
        folder_path = ""
        if parent_folder:
            parent_id = parent_folder.id
            folder_path = parent_folder.get_path()

        domain = Domain("located_on_the_server", "=", True) & Domain("folder_id", "=", parent_id)
        children = self.env["documents.document"].with_context(active_test=False).search(domain)
        for child in children:
            if not child._exist_on_the_server():
                # Do not delete the record if it is a spreadsheet itself
                if child.spreadsheet_data:
                    continue
                # Do not delete a folder that still contains spreadsheets inside
                if child.type == "folder":
                    has_spreadsheets_inside = bool(self.env["documents.document"].with_context(active_test=False).search_count([
                        ("folder_id", "child_of", child.id),
                        ("handler", "=", "spreadsheet"),
                    ]))
                    if has_spreadsheets_inside:
                        continue
                child.unlink()

        folder_full_path = os.path.join(self.root_path, folder_path)
        if os.path.isdir(folder_full_path):
            for child in os.listdir(folder_full_path):
                if os.path.isdir(os.path.join(folder_full_path, child)):
                    folder = self.create_folder(parent_id, child)
                    if recursive:
                        self.populate_folder(folder, recursive)
                elif not recursive and os.path.isfile(os.path.join(folder_full_path, child)):
                    self.create_file(parent_id, folder_full_path, child)

    @api.model
    @api.readonly
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        if len(domain) == 1 and len(domain[0]) == 3 and domain[0][0] == "folder_id":
            folder_id = domain[0][2]
            if isinstance(folder_id, str):
                doc = self.env["documents.document"].search([("name", "=", folder_id)])
            elif isinstance(folder_id, int):
                doc = self.env["documents.document"].search([("id", "=", folder_id)])
            if folder_id == "SERVER_FOLDER" or (doc.type == "folder" and doc.located_on_the_server):
                self.populate_folder(doc)
                if folder_id == "SERVER_FOLDER":
                    domain =[['located_on_the_server', '=', True], ['folder_id', '=', False], ['owner_id', '=', self.env.user.id]]
                else:
                    domain += [['owner_id', '=', self.env.user.id]]
        if (len(domain) == 3 and len(domain[0]) == 1 and domain[0] == "&" and len(domain[1]) == 3 and domain[1][0] == "folder_id" and
            domain[1][1] == "=" and len(domain[2]) == 3 and domain[2][0] == "owner_id" and domain[2][1] == "="):
            filter = ["located_on_the_server", "=", False]
            domain.append(filter)
        records = super().web_search_read(domain, specification, offset, limit, order, count_limit)
        return records

    def get_path(self):
        self.ensure_one()
        names = []
        parent_path_list = self.parent_path.split("/")[:-1]
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

    # Rok todo: check
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

    # Rok todo: check
    def write(self, vals):
        name = vals.get("name")
        if name and self.located_on_the_server:
            old_path = self.get_full_path()
            folder_path = os.path.dirname(old_path)
            new_path = os.path.join(folder_path, name)
            if old_path != new_path:
                os.rename(old_path, new_path)
        return super().write(vals)

    def action_archive(self):
        server_items = self.filtered("located_on_the_server")
        active_items = server_items.filtered(self._active_name)
        for item in active_items:
            path = item.get_full_path(check_exist=False)
            if path:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        super(DocumentsDocument, self - server_items).action_archive()

    def copy(self, default=None):
        server_items = self.filtered("located_on_the_server")
        server_files = server_items.filtered(lambda x: x.type != "folder")
        user_folder_id = default.get("user_folder_id")
        if server_files and isinstance(user_folder_id, str):
            folder = self.env["documents.document"].search([("id", "=", user_folder_id)])
            if folder.located_on_the_server:
                new_folder_path = folder.get_full_path()
                for file in server_files:
                    old_path = file.get_full_path()
                    new_path = os.path.join(new_folder_path, file.name)
                    shutil.copyfile(old_path, new_path)
        return super(DocumentsDocument, self - server_items).copy(default)

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

    def _extract_pdf_from_xml(self):
        self.ensure_one()
        if self.located_on_the_server:
            return False
        return super()._extract_pdf_from_xml()

    # Rok todo: check
    def _unzip_xlsx(self):
        if not self.located_on_the_server:
            return super()._unzip_xlsx()
        file = io.BytesIO(self.get_raw())
        if not zipfile.is_zipfile(file) or self.mimetype not in XLSX_MIME_TYPES:
            raise XSLXReadUserError(_("The file is not a xlsx file"))

        unzipped_size = 0
        with zipfile.ZipFile(file) as input_zip:
            if len(input_zip.infolist()) > 1000:
                raise XSLXReadUserError(_("The xlsx file is too big"))

            if "[Content_Types].xml" not in input_zip.namelist() or \
                    not any(name.startswith("xl/") for name in input_zip.namelist()):
                raise XSLXReadUserError(_("The xlsx file is corrupted"))

            unzipped = {}
            attachments = []
            for info in input_zip.infolist():
                if not (info.filename.endswith((".xml", ".xml.rels")) or "media/image" in info.filename) or\
                        not info.filename.startswith(SUPPORTED_PATHS):
                    # Don't extract files others than xmls or unsupported xmls
                    continue

                unzipped_size += info.file_size
                if unzipped_size > 50 * 1000 * 1000:  # 50MB
                    raise XSLXReadUserError(_("The xlsx file is too big"))

                if info.filename.endswith((".xml", ".xml.rels")):
                    unzipped[info.filename] = input_zip.read(info.filename).decode()
                elif "media/image" in info.filename:
                    image_file = input_zip.read(info.filename)
                    attachment = self._upload_image_file(image_file, info.filename)
                    attachments.append(attachment)
                    unzipped[info.filename] = {
                        "imageSrc": "/web/image/" + str(attachment.id),
                    }
        return unzipped, attachments

class XSLXReadUserError(UserError):
    pass
