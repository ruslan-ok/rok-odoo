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
        print("delete_migrated...")

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
        root_categ = self.env.ref("password_manager.password_category_all")
        rok_categ_name = "Migrated"
        rok_categ = self.env["password.category"].search([
            ("parent_id", "=", root_categ.id), 
            ("name", "=", rok_categ_name), 
        ])
        if not rok_categ:
            rok_categ = self.env["password.category"].create(
                {
                    "parent_id": root_categ.id, 
                    "name": rok_categ_name, 
                }
            )
        categ = self.migrate_groups_branch(connection, "store", rok_categ, item_id)
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
