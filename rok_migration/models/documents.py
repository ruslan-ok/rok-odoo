import os
from dotenv import load_dotenv
from odoo import models


class Article(models.Model):
    _name = "documents.document"
    _inherit = ["documents.document", "rok.migration.mixin"]

    def action_migrate_documents(self):
        print("Deleting previously migrated documents...")
        self.delete_migrated()

        print("Migrating knowledge articles...")
        self.do_migrate_docs()
        print("Done")

        action = self.env['ir.actions.act_window']._for_xml_id('documents.document_action')
        action['res_id'] = False
        return action


    def delete_migrated(self):
        projects_with_folder = self.env['project.project'].search([('use_documents', '=', True), ('documents_folder_id', '!=', False)])
        projects_folder_ids = projects_with_folder.mapped('documents_folder_id.id')
        my_docs = self.env["documents.document"].with_context(active_test=False).search([
            ("owner_id", "=", self.user.id), 
            ("res_model", "in", [False, "documents.document"]),
            ("id", "not in", projects_folder_ids), 
        ])
        my_docs.unlink()

    def do_migrate_docs(self):
        load_dotenv()
        STORAGE = os.getenv("STORAGE")

        storage = f"{STORAGE}/docs"
        info = {
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
                parent = self.get_parent(storage, root)
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
                    if DEBUG_LIMIT_FOLDERS and info["migrated"]["folders"] >= DEBUG_LIMIT_FOLDERS:
                        break
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

    def get_parent(self, storage, path):
        if path == storage:
            return self.env["documents.document"].sudo()
        else:
            parent_path = os.path.dirname(path)
            parent = self.env["documents.document"].search([
                ("owner_id", "=", self.user.id),
                ("type", "=", "folder"),
                ("folder_id", "=", self.get_parent(storage, parent_path).id),
                ("name", "=", os.path.basename(path)),
            ])
            return parent