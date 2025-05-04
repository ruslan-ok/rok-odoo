import os, paramiko
from dotenv import load_dotenv
from stat import S_ISDIR, S_ISREG
from odoo import models


class Article(models.Model):
    _name = "documents.document"
    _inherit = ["documents.document", "rok.migration.mixin"]

    def action_migrate_documents(self):
        owner = self.env["res.users"].search([("login", "=", "admin")])

        print("Deleting previously migrated documents...")
        self.delete_migrated(owner)

        print("Migrating knowledge articles...")
        self.do_migrate_docs(owner)
        print("Done")

        action = self.env['ir.actions.act_window']._for_xml_id('documents.document_action')
        action['res_id'] = False
        return action


    def delete_migrated(self, owner):
        my_docs = self.env["documents.document"].search([
            ("owner_id", "=", owner.id), 
        ])
        my_docs.unlink()

    def do_migrate_docs(self, owner):
        load_dotenv()
        HOST = os.getenv("DB_HOST")
        USER = os.getenv("DB_USER")
        PASSWORD = os.getenv("PASSWORD")
        STORAGE = os.getenv("STORAGE")
        ACCESS_MODE = os.getenv("ACCESS_MODE")

        root = self.env["documents.document"].sudo()
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
            "owner": owner,
        }
        if ACCESS_MODE == "ssh":
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.connect(HOST, username=USER, password=PASSWORD)
            sftp = client.open_sftp()
            print("Counting totals...")
            self.walk_remote(sftp, "get_totals", info, storage, root)
            print("Total folders: " + str(info["totals"]["folders"]))
            print("Total documents: " + str(info["totals"]["documents"]))
            print("Migrating documents...")
            self.walk_remote(sftp, "do_migrate", info, storage, root)
            client.close()
        else:
            print("Counting totals...")
            self.walk_local("get_totals", info, storage)
            print("Total folders: " + str(info["totals"]["folders"]))
            print("Total documents: " + str(info["totals"]["documents"]))
            print("Migrating documents...")
            self.walk_local("do_migrate", info, storage)

    def walk_remote(self, sftp, walk_mode, info, remote_dir, parent):
        DEBUG_LIMIT = int(os.getenv("DEBUG_LIMIT"))
        if DEBUG_LIMIT and info["migrated"]["documents"] >= DEBUG_LIMIT:
            return
        for entry in sftp.listdir_attr(remote_dir):
            if DEBUG_LIMIT and info["migrated"]["documents"] >= DEBUG_LIMIT:
                continue
            remote_path = os.path.join(remote_dir, entry.filename)
            mode = entry.st_mode
            if S_ISDIR(mode):
                if walk_mode == "get_totals":
                    info["totals"]["folders"] += 1
                    self.walk_remote(sftp, walk_mode, info, remote_path, parent)
                if walk_mode == "do_migrate":
                    folder = self.env["documents.document"].create({
                        "owner_id": info["owner"].id,
                        "folder_id": parent.id,
                        "name": entry.filename,
                        "type": "folder",
                    })
                    info["migrated"]["folders"] += 1
                    print(f"{info["migrated"]["folders"]}. Added folder: " + remote_path)
                    self.walk_remote(sftp, walk_mode, info, remote_path, folder.sudo())
            elif S_ISREG(mode):
                if walk_mode == "get_totals":
                    info["totals"]["documents"] += 1
                if walk_mode == "do_migrate":
                    AttachmentSudo = self.env['ir.attachment'] \
                        .sudo(not info["owner"]._is_internal()) \
                        .with_user(info["owner"]) \
                        .with_context(image_no_postprocess=True)
                    with sftp.file(remote_path, 'rb') as remote_file:
                        file_data = remote_file.read()
                        attachment = AttachmentSudo.create({
                            "name": entry.filename,
                            "raw": file_data,
                        })
                    vals = {
                        'attachment_id': attachment.id,
                        'type': 'binary',
                        'access_via_link': 'none' if parent.access_via_link in (False, 'none') else 'view',
                        'folder_id': parent.id,
                        'owner_id': info["owner"].id,
                        'res_model': "documents.document",
                    }
                    document_sudo = self.env["documents.document"].sudo().create(vals)
                    document_sudo.res_id = document_sudo.id
                    attachment.res_model = "documents.document"
                    attachment.res_id = document_sudo.id
                    info["migrated"]["documents"] += 1
                    print(f"{info["migrated"]["documents"]}. Added doc: " + remote_path)

    def walk_local(self, walk_mode, info, storage):
        DEBUG_LIMIT = int(os.getenv("DEBUG_LIMIT"))
        if DEBUG_LIMIT and info["migrated"]["documents"] >= DEBUG_LIMIT:
            return
        for root, dirs, files in os.walk(storage):
            if walk_mode == "do_migrate":
                parent = self.get_parent(info["owner"], storage, root)
            for name in dirs:
                path = os.path.join(root, name)
                if walk_mode == "get_totals":
                    info["totals"]["folders"] += 1
                if walk_mode == "do_migrate":
                    self.env["documents.document"].create({
                        "owner_id": info["owner"].id,
                        "folder_id": parent.id,
                        "name": name,
                        "type": "folder",
                    })
                    info["migrated"]["folders"] += 1
                    print(f"{info["migrated"]["folders"]}. Added folder: " + path)
            for name in files:
                if DEBUG_LIMIT and info["migrated"]["documents"] >= DEBUG_LIMIT:
                    break
                if name == ".DS_Store":
                    continue
                if walk_mode == "get_totals":
                    info["totals"]["documents"] += len(files)
                if walk_mode == "do_migrate":
                    path = os.path.join(root, name)
                    AttachmentSudo = self.env['ir.attachment'] \
                        .sudo(not info["owner"]._is_internal()) \
                        .with_user(info["owner"]) \
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
                        'owner_id': info["owner"].id,
                        'res_model': "documents.document",
                    }
                    document_sudo = self.env["documents.document"].sudo().create(vals)
                    document_sudo.res_id = document_sudo.id
                    attachment.res_model = "documents.document"
                    attachment.res_id = document_sudo.id
                    info["migrated"]["documents"] += 1
                    print(f"{info["migrated"]["documents"]}. Added doc: " + path)

    def get_parent(self, owner, storage, path):
        if path == storage:
            return self.env["documents.document"].sudo()
        else:
            parent_path = os.path.dirname(path)
            parent = self.env["documents.document"].search([
                ("owner_id", "=", owner.id),
                ("type", "=", "folder"),
                ("folder_id", "=", self.get_parent(owner, storage, parent_path).id),
                ("name", "=", os.path.basename(path)),
            ])
            return parent