import pg8000
from dotenv import load_dotenv
import os
import paramiko
from odoo import models


TASK_TASK_FIELDS = ["id", "name", "event", "start", "stop", "completed", "completion", "in_my_day", "important", "remind", "first_remind", "last_remind", "repeat", "repeat_num", "repeat_days", "categories", "info", "src_id", "app_task", "app_note", "app_news", "app_store", "app_doc", "app_warr", "app_expen", "app_trip", "app_fuel", "app_apart", "app_health", "app_work", "app_photo", "created", "last_mod", "active", "item_attr", "sort", "latitude", "longitude", "expen_qty", "expen_price", "expen_rate_usd", "expen_rate_eur", "expen_rate_gbp", "expen_usd", "expen_eur", "expen_gbp", "expen_kontr", "pers_dative", "trip_days", "trip_oper", "trip_price", "store_username", "store_value", "store_params", "apart_has_el", "apart_has_hw", "apart_has_cw", "apart_has_gas", "apart_has_ppo", "apart_has_tv", "apart_has_phone", "apart_has_zkx", "meter_el", "meter_hw", "meter_cw", "meter_ga", "meter_zkx", "price_service", "price_tarif", "price_border", "price_tarif2", "price_border2", "price_tarif3", "price_unit", "bill_residents", "bill_el_pay", "bill_tv_bill", "bill_tv_pay", "bill_phone_bill", "bill_phone_pay", "bill_zhirovka", "bill_hot_pay", "bill_repair_pay", "bill_zkx_pay", "bill_water_pay", "bill_gas_pay", "bill_rate", "bill_poo", "bill_poo_pay", "car_plate", "car_odometr", "car_notice", "fuel_volume", "fuel_price", "fuel_warn", "fuel_expir", "part_chg_km", "part_chg_mo", "repl_manuf", "repl_part_num", "repl_descr", "diagnosis", "bio_height", "bio_weight", "bio_temp", "bio_waist", "bio_systolic", "bio_diastolic", "bio_pulse", "months", "task_1_id", "task_2_id", "task_3_id", "user_id",]
GET_ITEMS_SQL = "SELECT * FROM task_task WHERE app_note != 0;"

GET_GROUPS_SQL = """
WITH RECURSIVE cte_group_id AS (
	SELECT group_id
	FROM task_taskgroup
	WHERE role = 'note'
		AND task_id = %s
)
, cte_group_ids(parent_id) AS (
	SELECT g.id 
	FROM task_group g 
	JOIN cte_group_id tg
		ON tg.group_id = g.id
	UNION ALL
	SELECT g.node_id 
	FROM task_group g, cte_group_ids sg 
	WHERE g.id = sg.parent_id
		AND sg.parent_id IS NOT NULL
)
, cte_groups AS (
	SELECT
		ROW_NUMBER() OVER() AS rn,
		g.id,
		g.name
	FROM task_group g
	JOIN cte_group_ids sg
		ON sg.parent_id = g.id
)
SELECT
	id,
	name
FROM cte_groups
ORDER BY rn;
"""
UPDATE_DATES_SQL = """
UPDATE knowledge_article
SET create_date = %s, write_date = %s
WHERE id = %s
"""
GET_URLS_SQL = """
SELECT href
FROM task_urls
WHERE task_id = %s
ORDER BY num;"""

class Article(models.Model):
    _inherit = "knowledge.article"

    def action_migrate_notes(self):
        print("Deleting previously migrated knowledge articles...")
        self.delete_migrated()

        print("Migrating knowledge articles...")
        self.do_migrate()
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

    def do_migrate(self):
        load_dotenv()

        # Database connection details
        DB_HOST = os.getenv("DB_HOST")
        DB_NAME = os.getenv("DB_NAME")
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_PORT = int(os.getenv("DB_PORT"))

        try:
            # Connect to the database
            connection = pg8000.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )

            cursor = connection.cursor()
            cursor.execute(GET_ITEMS_SQL)
            records = cursor.fetchall()
            note_article_map = {}
            for record in records:
                note_id = int(record[TASK_TASK_FIELDS.index("id")])
                article = self.migrate_item(connection, note_id, record)
                note_article_map[note_id] = article.id

            # Close the cursor and connection
            cursor.close()
            connection.close()            
            self.check_attachments(note_article_map)
        except Exception as e:
            print("An error occurred while connecting to the database:", e)

    def migrate_item(self, connection, note_id, row):
        group = self.migrate_item_groups(connection, note_id)
        user = self.env["res.users"].search([("login", "=", "admin")])
        body = self.prepare_body(connection, note_id, row[TASK_TASK_FIELDS.index("info")])
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
        self.env.cr.execute(UPDATE_DATES_SQL, (
            row[TASK_TASK_FIELDS.index("created")],
            row[TASK_TASK_FIELDS.index("last_mod")],
            article.id, 
        ))
        return article

    def migrate_item_groups(self, connection, note_id):
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
        group = rok_root
        cursor = connection.cursor()
        cursor.execute(GET_GROUPS_SQL, (note_id,))
        records = cursor.fetchall()
        for record in records:
            group = self.migrate_group(group, record)
        return group
    
    def migrate_group(self, parent, row):
        group_name = row[1]
        group = self.env["knowledge.article"].search([
            ("icon", "=", False), 
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
                    "internal_permission": "none",
                    "article_member_ids": [(0, 0, {
                        "partner_id": user.partner_id.id,
                        "permission": 'write'
                    })],
                }
            )
        return group
    
    def prepare_body(self, connection, note_id, body):
        lines = []
        last_line = ""
        counter = 0
        body = body.replace("\r\n", "\n") if body else ""
        src_lines = body.split("\n")
        for line in src_lines:
            if not line:
                counter += 1
            else:
                line = self.check_links(line)
                if not last_line:
                    last_line = line
                else:
                    if counter < 2:
                        last_line = last_line + "<br/>" + line
                    else:
                        lines.append(self.envelop(lines, last_line))
                        last_line = line
                counter = 0
        if last_line:
            lines.append(self.envelop(lines, last_line))

        cursor = connection.cursor()
        cursor.execute(GET_URLS_SQL, (note_id,))
        records = cursor.fetchall()
        urls = []
        for record in records:
            if record:
                urls.append(self.check_links(record[0]))
        if len(urls):
            lines.append(self.envelop(lines, "URLs:<br/>" + "".join(urls)))
        return "".join(lines)
    
    def envelop(self, lines, line):
        if not lines:
            return '<p data-oe-version="1.2">' + line + "</p>"
        return '<p>' + line + "</p>"
    
    def check_links(self, line):
        parts = line.split("https://")
        if len(parts) > 1:
            part_1 = parts[0]
            part_2 = parts[1].split(" ")[0]
            line = part_1 + '<a href="https://' + part_2 + '">' + part_2 + "</a>"
        parts = line.split("http://")
        if len(parts) > 1:
            part_1 = parts[0]
            part_2 = parts[1].split(" ")[0]
            line = part_1 + '<a href="http://' + part_2 + '">' + part_2 + "</a>"
        return line
    
    def check_attachments(self, note_article_map):
        print("Checking for attachments started...")
        HOST = os.getenv("DB_HOST")
        USER = os.getenv("DB_USER")
        PASSWORD = os.getenv("PASSWORD")
        STORAGE = os.getenv("STORAGE")
        user = self.env["res.users"].search([("login", "=", "admin")])

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.connect(HOST, username=USER, password=PASSWORD)
        sftp = client.open_sftp()
        remote_path = "%s/attachments/note/" % STORAGE
        dir_command = 'find %s -name "note_*"' % remote_path
        _, dir_stdout, _ = client.exec_command(dir_command)
        for dir_line in dir_stdout:
            note_id = int(dir_line.strip('\n').replace(remote_path, "").replace("note_", ""))
            article_id = note_article_map.get(note_id, False)
            if not article_id:
                continue
            file_command = 'find %snote_%s -name "*"' % (remote_path, note_id)
            _, file_stdout, _ = client.exec_command(file_command)
            for file_line in file_stdout:
                filename = file_line.strip('\n').replace(f"{remote_path}note_{note_id}", "")
                if filename:
                    if filename.startswith("/"):
                        filename = filename[1:]
                    with sftp.file(f"{remote_path}note_{note_id}/{filename}",'rb') as remote_file:
                        file_data = remote_file.read()
                        self.env["ir.attachment"].sudo().with_user(user).create({
                            "name": filename,
                            "raw": file_data,
                            "res_model": "knowledge.article",
                            "res_id": article_id,
                        })
                        print(f"Attachment {filename} added to article {article_id}")
        print("Checking for attachments finished.")
        client.close()

