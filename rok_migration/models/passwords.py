import json
from markupsafe import Markup
from odoo import models
from .rok_migration_mixin import TASK_TASK_FIELDS

GET_ITEMS_SQL = "SELECT * FROM task_task WHERE app_store != 0;"


class Passwords(models.Model):
    _name = "passwords"
    _inherit = ["passwords", "rok.migration.mixin"]

    def action_migrate_passwords(self):
        print("Deleting previously migrated passwords...")
        self.delete_migrated()

        print("Migrating passwords...")
        self.do_migrate(GET_ITEMS_SQL, "store")
        print("Done")

        action = self.env['ir.actions.act_window']._for_xml_id('password_manager.passwords_action')
        action['res_id'] = False
        return action

    def delete_migrated(self):
        passwords = self.env["passwords"].search([])
        passwords.unlink()

    def migrate_item(self, connection, item_id, row):
        categ = self.migrate_item_groups(connection, item_id)
        body = self.prepare_body(connection, item_id, row[TASK_TASK_FIELDS.index("info")])
        password = self.env["passwords"].create(
            {
                "title": row[TASK_TASK_FIELDS.index("name")], 
                "login": row[TASK_TASK_FIELDS.index("store_username")], 
                "value": row[TASK_TASK_FIELDS.index("store_value")], 
                "info": body, 
                "categ_id": categ.id, 
                "active": not row[TASK_TASK_FIELDS.index("completed")],
            }
        )
        self.update_create_date("passwords", password.id, row)
        return password

    def migrate_item_groups(self, connection, item_id):
        root_category = self.env["password.category"]
        categ = self.migrate_groups_branch(connection, "store", root_category, item_id)
        return categ

    def migrate_group(self, parent, row):
        categ_name = row[1]
        categ = self.env["password.category"].search([
            ("parent_id", "=", parent.id), 
            ("name", "=", categ_name), 
        ])
        if not categ:
            categ = self.env["password.category"].create(
                {
                    "parent_id": parent.id, 
                    "name": categ_name, 
                }
            )
        return categ

    def update_item_with_attachments(self, item_id):
        password = self.env["passwords"].browse(item_id)
        attachments = self.env["ir.attachment"].search([("res_id", "=", item_id), ("res_model", "=", "passwords")])
        body = str(password.info)
        if not body:
            part_1 = '<p  data-oe-version="1.2">'
        else:
            parts = body.split("</p>")
            part_1 = "".join(parts[:-1])
        if part_1 and attachments:
            attach_info = "<p>Attachments:<br/>"
            for attach in attachments:
                info = attach._get_media_info()
                access_token = attach.generate_access_token()[0]
                if attach.mimetype.startswith("image/"):
                    attach_info += '<img class="img-fluid" data-file-name="%s" src="%s?access_token=%s"><br/>' % (info["name"], info["image_src"], access_token)
                else:
                    props = json.dumps({
                        "fileData": {
                            "access_token": access_token,
                            "checksum": info["checksum"],
                            "extension": info["name"].split(".")[-1:][0],
                            "filename": info["name"],
                            "id": info["id"],
                            "mimetype": info["mimetype"],
                            "name": info["name"],
                            "type": info["type"],
                            "url": info["url"] if info["url"] else "",
                        }
                    })
                    attach_info += '<span data-embedded="file" class="o_file_box o-contenteditable-false" data-embedded-props=%s></span><br/>' % ("'" + props + "'")
            password.info = Markup(part_1 + attach_info + "</p>")
