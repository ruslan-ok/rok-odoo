import pg8000
from dotenv import load_dotenv
import os
from odoo import models

TASK_TASK_FIELDS = [
    "id", "name", "event", "start", "stop", "completed", "completion", "in_my_day", "important", "remind", "first_remind", "last_remind", 
    "repeat", "repeat_num", "repeat_days", "categories", "info", "src_id", "app_task", "app_note", "app_news", "app_store", "app_doc", 
    "app_warr", "app_expen", "app_trip", "app_fuel", "app_apart", "app_health", "app_work", "app_photo", "created", "last_mod", "active", 
    "item_attr", "sort", "latitude", "longitude", "expen_qty", "expen_price", "expen_rate_usd", "expen_rate_eur", "expen_rate_gbp", 
    "expen_usd", "expen_eur", "expen_gbp", "expen_kontr", "pers_dative", "trip_days", "trip_oper", "trip_price", "store_username", 
    "store_value", "store_params", "apart_has_el", "apart_has_hw", "apart_has_cw", "apart_has_gas", "apart_has_ppo", "apart_has_tv", 
    "apart_has_phone", "apart_has_zkx", "meter_el", "meter_hw", "meter_cw", "meter_ga", "meter_zkx", "price_service", "price_tarif", 
    "price_border", "price_tarif2", "price_border2", "price_tarif3", "price_unit", "bill_residents", "bill_el_pay", "bill_tv_bill", 
    "bill_tv_pay", "bill_phone_bill", "bill_phone_pay", "bill_zhirovka", "bill_hot_pay", "bill_repair_pay", "bill_zkx_pay", 
    "bill_water_pay", "bill_gas_pay", "bill_rate", "bill_poo", "bill_poo_pay", "car_plate", "car_odometr", "car_notice", "fuel_volume", 
    "fuel_price", "fuel_warn", "fuel_expir", "part_chg_km", "part_chg_mo", "repl_manuf", "repl_part_num", "repl_descr", "diagnosis", 
    "bio_height", "bio_weight", "bio_temp", "bio_waist", "bio_systolic", "bio_diastolic", "bio_pulse", "months", "task_1_id", "task_2_id", 
    "task_3_id", "user_id",
]

GET_ROK_GROUPS_SQL = """
    WITH RECURSIVE cte_group_id AS (
        SELECT group_id
        FROM task_taskgroup
        WHERE role = %s
            AND task_id = %s
    )
    , cte_group_ids(num, parent_id) AS (
        SELECT 1 as num, g.id 
        FROM task_group g 
        JOIN cte_group_id tg
            ON tg.group_id = g.id
        UNION ALL
        SELECT num+1 as num, g.node_id 
        FROM task_group g, cte_group_ids sg 
        WHERE g.id = sg.parent_id
            AND sg.parent_id IS NOT NULL
    )
    , cte_groups AS (
        SELECT
            sg.num,
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
    ORDER BY num DESC;
"""

GET_URLS_SQL = """
    SELECT href
    FROM task_urls
    WHERE task_id = %s
    ORDER BY num;
"""


class RokMigrationMixin(models.AbstractModel):
    _name = "rok.migration.mixin"
    _description = "Rok Migration Mixin"

    @property
    def user(self):
        return self.env.user

    def do_migrate(self, get_items_sql, role):
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
            cursor.execute(get_items_sql)
            rows = cursor.fetchall()
            items_map = {}
            for row in rows:
                item_id = int(row[TASK_TASK_FIELDS.index("id")])
                new_item = self.migrate_item(connection, item_id, row)
                if new_item:
                    items_map[item_id] = new_item.id

            # Close the cursor and connection
            cursor.close()
            connection.close()
            self.check_attachments(items_map, role)
        except Exception as e:
            print("An error occurred while connecting to the database:", e)

    def migrate_groups_branch(self, connection, role, root, item_id):
        group = root
        cursor = connection.cursor()
        cursor.execute(GET_ROK_GROUPS_SQL, (role, item_id,))
        records = cursor.fetchall()
        for record in records:
            group = self.migrate_group(group, record)
        return group

    def prepare_body(self, connection, item_id, body):
        lines = []
        last_line = ""
        counter = 0
        src_lines = []
        if body:
            body = body.replace("\r\n", "\n")
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
        cursor.execute(GET_URLS_SQL, (item_id,))
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
        if not line:
            return line
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

    def check_attachments(self, items_map, role):
        print("Checking for attachments started...")
        STORAGE = os.getenv("STORAGE")
        storage_dir = os.path.join(STORAGE, "attachments", role)

        for root, dirs, files in os.walk(storage_dir):
            if root == storage_dir:
                continue
            item_id = int(os.path.basename(root).replace(f"{role}_", ""))
            new_item_id = items_map.get(item_id, False)
            if not new_item_id:
                continue
            for dir in dirs:
                raise ValueError(f"Directory {dir} is not expected.")
            for file in files:
                filename = os.path.join(root, file)
                with open(filename, 'rb') as f:
                    file_data = f.read()
                    self.env["ir.attachment"].sudo().with_user(self.user).create({
                        "name": file,
                        "raw": file_data,
                        "res_model": self._name,
                        "res_id": new_item_id,
                    })
                    print(f"Attachment for {self._name}({new_item_id}): {file}")
            self.update_item_with_attachments(new_item_id)
        print("Checking for attachments finished.")

    def update_create_date(self, table, item_id, row):
        UPDATE_DATES_SQL = f"""
            UPDATE {table}
            SET create_date = %s, write_date = %s
            WHERE id = %s
        """
        created = row[TASK_TASK_FIELDS.index("created")],
        last_mod = row[TASK_TASK_FIELDS.index("last_mod")],
        self.env.cr.execute(UPDATE_DATES_SQL, (created, last_mod, item_id))
