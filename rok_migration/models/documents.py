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

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.connect(HOST, username=USER, password=PASSWORD)
        sftp = client.open_sftp()
        remote_path = "%s/docs" % STORAGE
        root = self.env["documents.document"].sudo()
        counter = 0
        self.walk_remote(sftp, remote_path, owner, root, counter)
        client.close()

    def walk_remote(self, sftp, remotedir, owner, parent, counter):
        for entry in sftp.listdir_attr(remotedir):
            remotepath = remotedir + "/" + entry.filename
            mode = entry.st_mode
            if S_ISDIR(mode):
                folder = self.env["documents.document"].create({
                    "owner_id": owner.id,
                    "folder_id": parent.id,
                    "name": entry.filename,
                    "type": "folder",
                })
                print(f"{counter}. Added folder: " + remotepath)
                self.walk_remote(sftp, remotepath, owner, folder.sudo(), counter)
            elif S_ISREG(mode):
                if counter > 10:
                    continue
                AttachmentSudo = self.env['ir.attachment'] \
                    .sudo(not owner._is_internal()) \
                    .with_user(owner) \
                    .with_context(image_no_postprocess=True)
                with sftp.file(remotepath, 'rb') as remote_file:
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
                    'owner_id': owner.id,
                    'res_model': "documents.document",
                }
                document_sudo = self.env["documents.document"].sudo().create(vals)
                document_sudo.res_id = document_sudo.id
                attachment.res_model = "documents.document"
                attachment.res_id = document_sudo.id
                print(f"{counter}. Added doc: " + remotepath)
                counter += 1
