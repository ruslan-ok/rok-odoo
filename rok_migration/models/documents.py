import logging
import os
from dotenv import load_dotenv
from odoo import models

_logger = logging.getLogger(__name__)


class Article(models.Model):
    _name = "documents.document"
    _inherit = ["documents.document", "rok.migration.mixin"]

    def action_migrate_documents(self):
        print("Deleting previously migrated documents...")
        self.delete_migrated()

        print("Migrating documents and photos...")
        self.do_migrate_docs()
        print("Done")

        action = self.env['ir.actions.act_window']._for_xml_id('documents.document_action')
        action['res_id'] = False
        return action


    def delete_migrated(self):
        _logger.info("Deleting previously migrated documents...")
        # Delete documents that are owned by the user and not in any project folder
        if not self.user:
            _logger.warning("No user found, skipping deletion of migrated documents.")
            return
        if not self.user._is_internal():
            _logger.warning("User is not internal, skipping deletion of migrated documents.")
            return
        # Get the user's documents that are not in any project folder
        my_docs = self.env["documents.document"].with_context(active_test=False).search([
            ("owner_id", "=", self.user.id), 
            ("res_model", "in", [False, "documents.document"]),
        ])
        _logger.info(f"Found {len(my_docs)} documents owned by the user {self.user.name}.")
        _logger.info(str(my_docs.ids))
        projects_with_folder = self.env['project.project'].search([('use_documents', '=', True), ('documents_folder_id', 'child_of', my_docs.ids)])
        _logger.info(f"Found {len(projects_with_folder)} projects with documents folders.")
        projects_folder_ids = projects_with_folder.mapped('documents_folder_id.id')
        _logger.info(str(projects_folder_ids))
        # Exclude documents that are in project folders and not in the root folder
        my_docs = my_docs.filtered(lambda doc: doc.id not in projects_folder_ids and (not doc.folder_id or doc.folder_id.id not in projects_folder_ids))
        _logger.info(f"Deleting {len(my_docs)} documents owned by the user {self.user.name} that are not in any project folder.")
        _logger.info(str(my_docs.ids))
        my_docs.unlink()

    def do_migrate_docs(self):
        load_dotenv()
        STORAGE = os.getenv("STORAGE")

        sources = ["docs", "photo"]

        for source in sources:
            storage = f"{STORAGE}/{source}"
            if not os.path.exists(storage):
                print(f"Storage path {storage} does not exist.")
                continue
            info = {
                "source": source,
                "totals": {
                    "folders": 0,
                    "documents": 0,
                },
                "migrated": {
                    "folders": 0,
                    "documents": 0,
                },
            }
            print("Counting totals...")
            self.walk_local("get_totals", info, storage)
            print("Total folders: " + str(info["totals"]["folders"]))
            print("Total documents: " + str(info["totals"]["documents"]))
            print("Migrating documents...")
            self.walk_local("do_migrate", info, storage)

    def walk_local(self, walk_mode, info, storage):
        DEBUG_LIMIT_DOCS = int(os.getenv("DEBUG_LIMIT_DOCS"))
        DEBUG_LIMIT_FOLDERS = int(os.getenv("DEBUG_LIMIT_FOLDERS"))
        for root, dirs, files in os.walk(storage):
            if walk_mode == "do_migrate":
                parent = self.get_parent(storage, root, info["source"])
            for name in dirs:
                path = os.path.join(root, name)
                if walk_mode == "get_totals":
                    info["totals"]["folders"] += 1
                if walk_mode == "do_migrate":
                    if DEBUG_LIMIT_FOLDERS and info["migrated"]["folders"] >= DEBUG_LIMIT_FOLDERS:
                        break
                    if DEBUG_LIMIT_DOCS and info["migrated"]["documents"] >= DEBUG_LIMIT_DOCS:
                        break
                    self.env["documents.document"].create({
                        "owner_id": self.user.id,
                        "folder_id": parent.id,
                        "name": name,
                        "type": "folder",
                    })
                    info["migrated"]["folders"] += 1
                    print(f"{info["migrated"]["folders"]}. Added folder: " + path)
            for name in files:
                if name == ".DS_Store":
                    continue
                if walk_mode == "get_totals":
                    info["totals"]["documents"] += len(files)
                if walk_mode == "do_migrate":
                    if DEBUG_LIMIT_DOCS and info["migrated"]["documents"] >= DEBUG_LIMIT_DOCS:
                        break
                    path = os.path.join(root, name)
                    AttachmentSudo = self.env['ir.attachment'] \
                        .sudo(not self.user._is_internal()) \
                        .with_user(self.user) \
                        .with_context(image_no_postprocess=True)
                    with open(path, 'rb') as file:
                        file_data = file.read()
                        attachment = AttachmentSudo.create({
                            "name": name,
                            "raw": file_data,
                        })
                    vals = {
                        'attachment_id': attachment.id,
                        'type': 'binary',
                        'access_via_link': 'none' if parent.access_via_link in (False, 'none') else 'view',
                        'folder_id': parent.id,
                        'owner_id': self.user.id,
                        'res_model': "documents.document",
                    }
                    document_sudo = self.env["documents.document"].sudo().create(vals)
                    document_sudo.res_id = document_sudo.id
                    attachment.res_model = "documents.document"
                    attachment.res_id = document_sudo.id
                    info["migrated"]["documents"] += 1
                    print(f"{info["migrated"]["documents"]}. Added doc: " + path)

    def get_parent(self, storage, path, source=None):
        if path == storage:
            parent = self.env["documents.document"].search([
                ("owner_id", "=", self.user.id),
                ("type", "=", "folder"),
                ("folder_id", "=", False),
                ("name", "=", source),
            ])
            if not parent:
                parent = self.env["documents.document"].create({
                    "owner_id": self.user.id,
                    "type": "folder",
                    "folder_id": False,
                    "name": source,
                })
        else:
            parent_path = os.path.dirname(path)
            parent = self.env["documents.document"].search([
                ("owner_id", "=", self.user.id),
                ("type", "=", "folder"),
                ("folder_id", "=", self.get_parent(storage, parent_path, source).id),
                ("name", "=", os.path.basename(path)),
            ])
        return parent.sudo()
