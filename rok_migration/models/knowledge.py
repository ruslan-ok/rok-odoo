import json
from markupsafe import Markup
from odoo import models
from .rok_migration_mixin import TASK_TASK_FIELDS

GET_ITEMS_SQL = "SELECT * FROM task_task WHERE app_note != 0;"


class Article(models.Model):
    _name = "knowledge.article"
    _inherit = ["knowledge.article", "rok.migration.mixin"]

    def action_migrate_notes(self):
        print("Deleting previously migrated knowledge articles...")
        self.delete_migrated()

        print("Migrating knowledge articles...")
        self.do_migrate(GET_ITEMS_SQL, "note")
        print("Done")

        article = self[0] if self else False
        if not article and self.env.context.get('res_id', False):
            article = self.browse([self.env.context["res_id"]])
        if not article:
            article = self._get_first_accessible_article()

        action = self.env['ir.actions.act_window']._for_xml_id('knowledge.knowledge_article_action_form')
        action['res_id'] = article.id
        return action


    def delete_migrated(self):
        rok_roots = self.env["knowledge.article"].search([
            ("icon", "=", False), 
            ("category", "=", "private"), 
            ("parent_id", "=", False), 
            ("name", "=", "notes"), 
        ])
        rok_articles = self.env["knowledge.article"].search([
            ("root_article_id", "in", rok_roots.ids), 
        ])
        rok_articles.unlink()

    def migrate_item(self, connection, item_id, row):
        group = self.migrate_item_groups(connection, item_id)
        user = self.env["res.users"].search([("login", "=", "admin")])
        body = self.prepare_body(connection, item_id, row[TASK_TASK_FIELDS.index("info")])
        article = self.env["knowledge.article"].create(
            {
                "parent_id": group.id, 
                "category": "private", 
                "name": row[TASK_TASK_FIELDS.index("name")],
                "body": body, 
                "active": not row[TASK_TASK_FIELDS.index("completed")],
                "internal_permission": "none",
                "article_member_ids": [(0, 0, {
                    "partner_id": user.partner_id.id,
                    "permission": 'write'
                })],
            }
        )
        self.update_create_date("knowledge_article", article.id, row)
        return article

    def migrate_item_groups(self, connection, item_id):
        root_name = "notes"
        rok_root = self.env["knowledge.article"].search([
            ("icon", "=", False), 
            ("category", "=", "private"), 
            ("parent_id", "=", False), 
            ("name", "=", root_name), 
        ])
        if not rok_root:
            user = self.env["res.users"].search([("login", "=", "admin")])
            rok_root = self.env["knowledge.article"].create(
                {
                    "parent_id": False, 
                    "category": "private", 
                    "name": root_name, 
                    "internal_permission": "none",
                    "article_member_ids": [(0, 0, {
                        "partner_id": user.partner_id.id,
                        "permission": 'write'
                    })],
                }
            )
        group = self.migrate_groups_branch(connection, "note", rok_root, item_id)
        return group
    
    def migrate_group(self, parent, row):
        group_name = row[1]
        group = self.env["knowledge.article"].search([
            ("category", "=", "private"), 
            ("parent_id", "=", parent.id), 
            ("name", "=", group_name), 
        ])
        if not group:
            user = self.env["res.users"].search([("login", "=", "admin")])
            group = self.env["knowledge.article"].create(
                {
                    "parent_id": parent.id, 
                    "category": "private", 
                    "name": group_name, 
                    "icon": "📁",
                    "internal_permission": "none",
                    "article_member_ids": [(0, 0, {
                        "partner_id": user.partner_id.id,
                        "permission": 'write'
                    })],
                }
            )
        return group
    
    def update_item_with_attachments(self, item_id):
        article = self.env["knowledge.article"].browse(item_id)
        attachments = self.env["ir.attachment"].search([("res_id", "=", item_id)])
        body = str(article.body)
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
            article.body = Markup(part_1 + attach_info + "</p>")
