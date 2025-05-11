import datetime
from markupsafe import Markup
from odoo import models, Command
from .rok_migration_mixin import TASK_TASK_FIELDS

SOURCES = {
    "todo": {
        "filter_field": "app_task",
        "role": "todo",
    },
    "news": {
        "filter_field": "app_news",
        "role": "news",
    },
}

GET_ITEMS_SQL = """
SELECT * 
FROM task_task 
WHERE COALESCE(%s, 0) != 0 AND (COALESCE(repeat, 0) = 0 OR completed = FALSE);
"""
GET_STEPS_SQL = "SELECT * FROM task_step WHERE task_id = %s;"
EMBED_TEMPLATE = """
<span class="o_file_box o-contenteditable-false">
    <span class="d-flex flex-grow-1 align-items-center alert alert-info">
        <span class="o_file_image d-flex o_image user-select-none"
            title="%(filename)s" data-mimetype="%(mimetype)s"/>
        <span class="o_file_name_container mx-2">
            <a class="o_link_readonly o-contenteditable-true" href="%(downloadUrl)s">%(filename)s</a>
        </span>
    </span>
</span>
"""
GET_ROK_GROUPS_SQL = """
    WITH RECURSIVE cte_group_id_pre AS (
        SELECT group_id, role
        FROM task_taskgroup
        WHERE role in ('todo', 'news')
            AND task_id = %s
    )
	, cte_group_id AS (
		SELECT group_id, role
		FROM cte_group_id_pre
		ORDER BY role DESC
		LIMIT 1
	)
	, cte_period_1 AS (
		SELECT
			MIN(COALESCE(t.start, CASE WHEN t.completed THEN t.completion ELSE t.stop END)) AS start,
			MAX(COALESCE(CASE WHEN t.completed THEN t.completion ELSE t.stop END, NOW()::DATE + 7)) AS stop
		FROM cte_group_id g
		JOIN task_taskgroup tg
			ON g.group_id = tg.group_id
		JOIN task_task t
			ON tg.task_id = t.id
		WHERE 1=1
			AND t.app_task != 0 
			AND (COALESCE(t.repeat, 0) = 0 OR t.completed = FALSE)
	)
	, cte_period_2 AS (
		SELECT
			MIN(COALESCE(t.start, CASE WHEN t.completed THEN t.completion ELSE t.stop END)) AS start,
			MAX(COALESCE(CASE WHEN t.completed THEN t.completion ELSE t.stop END, NOW()::DATE + 7)) AS stop
		FROM task_task t
		WHERE 1=1
			AND t.app_task != 0 
			AND (COALESCE(t.repeat, 0) = 0 OR t.completed = FALSE)
			AND t.id NOT IN (SELECT task_id FROM task_taskgroup WHERE role = 'todo')
	)
	, cte_period AS (
		SELECT 
			COALESCE(p1.start, p2.start) AS start,
			COALESCE(p1.stop, p2.stop) AS stop
		FROM cte_period_1 p1, cte_period_2 p2
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
    , cte_groups_1 AS (
        SELECT
            sg.num,
			g.id,
            g.name,
			g.role
        FROM task_group g
        JOIN cte_group_ids sg
            ON sg.parent_id = g.id
    )
	, cte_groups AS (
		SELECT
			COALESCE(string_agg(g.name, ' / '), 'Undefined') AS name,
			MAX(g.role) as role
		FROM cte_groups_1 g
	)
    SELECT
		p.start,
		p.stop,
        string_agg(g.name, ' / ') as name,
		COALESCE(g.role, CASE WHEN COALESCE(t.app_task, 0) != 0 THEN 'todo' ELSE 'news' END) AS role
    FROM cte_period p, cte_groups g, task_task t
	WHERE t.id = %s
	GROUP BY 
		p.start,
		p.stop,
		COALESCE(g.role, CASE WHEN COALESCE(t.app_task, 0) != 0 THEN 'todo' ELSE 'news' END);
"""



class Task(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "rok.migration.mixin"]

    def action_migrate_tasks(self):
        print("Deleting previously migrated tasks...")
        self.delete_migrated()

        print("Migrating tasks...")
        for source in SOURCES:
            filter_field = SOURCES[source]["filter_field"]
            role = SOURCES[source]["role"]
            self.do_migrate(GET_ITEMS_SQL % filter_field, role)
        print("Done")

        action = self.env['ir.actions.act_window']._for_xml_id('project.action_view_task')
        action['res_id'] = False
        return action


    def delete_migrated(self):
        rok_cal_tag = self.env["calendar.event.type"].search([
            ("name", "=", "rok"), 
        ])
        if rok_cal_tag:
            rok_cal_events = self.env["calendar.event"].with_context(active_test=False).search([
                ("user_id", "=", self.user.id), 
                ("categ_ids", "in", rok_cal_tag.ids), 
            ])
            rok_cal_events.unlink()

        rok_tag = self.env["project.tags"].search([
            ("name", "=", "rok"), 
        ])
        if rok_tag:
            rok_tasks = self.env["project.task"].with_context(active_test=False).search([
                ("user_ids", "in", self.user.ids), 
                ("tag_ids", "in", rok_tag.ids), 
            ])
            rok_tasks.unlink()
            rok_projects = self.env["project.project"].with_context(active_test=False).search([
                ("user_id", "=", self.user.id), 
                ("tag_ids", "in", rok_tag.ids), 
            ])
            rok_projects.unlink()

    def migrate_item(self, connection, item_id, row):
        project, role = self.migrate_project(connection, item_id)
        if not project:
            return
        res_model_id=self.env['ir.model']._get_id("project.task")
        body = self.prepare_body(connection, item_id, row[TASK_TASK_FIELDS.index("info")])
        category_names = ["rok", role]
        task_category_names = category_names.copy()
        categories = row[TASK_TASK_FIELDS.index("categories")]
        if categories:
            task_category_names += categories.split()
        tags = self.get_tags_by_names(task_category_names)
        completed = row[TASK_TASK_FIELDS.index("completed")]
        repeat_units = ["no", "day", "day", "week", "month", "year"]
        repeat = row[TASK_TASK_FIELDS.index("repeat")] or 0
        recurrence = self.env["project.task.recurrence"]
        if repeat != 0:
            recurrence = self.env["project.task.recurrence"].search([
                ("repeat_interval", "=", repeat), 
                ("repeat_unit", "=", repeat_units[repeat]),
                ("repeat_type", "=", "forever"),
            ])
            if not recurrence:
                recurrence = self.env["project.task.recurrence"].create({
                    "repeat_interval": repeat,
                    "repeat_unit": repeat_units[repeat],
                    "repeat_type": "forever",
                })
        stop_date = row[TASK_TASK_FIELDS.index("stop")]
        if stop_date:
            stop_date = stop_date.replace(tzinfo=None)
        last_mod_date = row[TASK_TASK_FIELDS.index("last_mod")]
        if last_mod_date:
            last_mod_date = last_mod_date.replace(tzinfo=None)
        task_name = row[TASK_TASK_FIELDS.index("name")]

        task_vals = {
            "active": not project.name.startswith("Корзина / "),
            "name": task_name,
            "description": body,
            "priority": "1" if row[TASK_TASK_FIELDS.index("important")] else "0",
            "tag_ids": [Command.set(tags.ids)],
            "state": "1_done" if completed else "1_done" if role == "news" else "01_in_progress",
            "date_deadline": stop_date,
            "date_last_stage_update": stop_date if completed else last_mod_date,
            "project_id": project.id, 
            "user_ids": [Command.link(self.user.id)],
            "recurring_task": repeat != 0,
            "recurrence_id": recurrence.id,
        }
        subtasks_vals = self.get_subtasks_vals(connection, item_id, task_vals)
        if subtasks_vals:
            task_vals["child_ids"] = [Command.create(vals) for vals in subtasks_vals]
        task = self.env["project.task"].create(task_vals)
        self.update_create_date("project_task", task.id, row)

        if role == "todo" and not completed and stop_date:
            cal_tags = self.get_cal_tags_by_names(category_names)
            cal_vals = {
                "name": task_name,
                "start": stop_date - datetime.timedelta(hours=1),
                "stop": stop_date,
                "user_id": self.user.id,
                "description": body,
                "res_model_id": res_model_id,
                "res_id": task.id,
                "categ_ids": [Command.set(cal_tags.ids)],
            }

            remind = row[TASK_TASK_FIELDS.index("remind")]
            if remind:
                remind = remind.replace(tzinfo=None)
                if remind < stop_date:
                    cal_vals["start"] = remind

            self.env["calendar.event"].create(cal_vals)
            print(f"Created calendar event: {cal_vals["start"].date()} {cal_vals["name"]}")

        return task

    def get_tags_by_names(self, names):
        tag_ids = []
        if "rok" not in names:
            names.append("rok")
        for name in names:
            tag = self.env["project.tags"].search([("name", "=", name)])
            if not tag:
                tag = self.env["project.tags"].create({"name": name})
            tag_ids.append(tag.id)
        return self.env["project.tags"].browse(tag_ids)
    
    def get_cal_tags_by_names(self, names):
        tag_ids = []
        if "rok" not in names:
            names.append("rok")
        for name in names:
            tag = self.env["calendar.event.type"].search([("name", "=", name)])
            if not tag:
                tag = self.env["calendar.event.type"].create({"name": name})
            tag_ids.append(tag.id)
        return self.env["calendar.event.type"].browse(tag_ids)
    
    def get_subtasks_vals(self, connection, item_id, task_vals):
        cursor = connection.cursor()
        cursor.execute(GET_STEPS_SQL, (item_id,))
        rows = cursor.fetchall()
        subtasks_vals = []
        for row in rows:
            subtask_vals = {
                "active": task_vals["active"],
                "name": row[3],
                "priority": "0",
                "state": "1_done" if row[4] else "01_in_progress",
                "project_id": task_vals["project_id"], 
                "user_ids": task_vals["user_ids"],
            }
            subtasks_vals.append(subtask_vals)
        return subtasks_vals
        
    def migrate_project(self, connection, item_id):
        cursor = connection.cursor()
        cursor.execute(GET_ROK_GROUPS_SQL, (item_id, item_id))
        project_info = cursor.fetchall()
        project_name = project_info[0][2]
        role = project_info[0][3]
        if not project_name:
            return None, None
        if project_name.startswith("Корзина / ") or " / Корзина / " in project_name:
            return None, None
        tag_names = [role, "rok"]
        tags = self.get_tags_by_names(tag_names)
        project = self.env["project.project"].search([
            ("user_id", "=", self.user.id), 
            ("name", "=", project_name), 
            ("tag_ids", "in", tags.ids),
        ])
        if not project:
            project_start = project_info[0][0].replace(tzinfo=None)
            project_stop = project_info[0][1].replace(tzinfo=None)
            project = self.env["project.project"].create(
                {
                    "user_id": self.user.id,
                    "name": project_name, 
                    "date_start": project_start, 
                    "date": project_stop, 
                    "privacy_visibility": "followers",
                    "tag_ids": [Command.set(tags.ids)],
                }
            )
        return project, role
    
    def update_item_with_attachments(self, item_id):
        item = self.env["project.task"].browse(item_id)
        attachments = self.env["ir.attachment"].search([("res_id", "=", item_id)])
        body = str(item.description)
        if not body:
            part_1 = '<p  data-oe-version="1.2">'
        else:
            parts = body.split("</p>")
            part_1 = "".join(parts[:-1])
        if part_1 and attachments:
            attach_info = "<p>Attachments:<br/>"
            for attachment in attachments:
                info = attachment._get_media_info()
                access_token = attachment.generate_access_token()[0]
                if attachment.mimetype.startswith("image/"):
                    attach_info += '<img class="img-fluid" data-file-name="%s" src="%s?access_token=%s"><br/>' % \
                        (info["name"], info["image_src"], access_token)
                else:
                    download_url = f"/web/content/{attachment.id}?unique={attachment.checksum}&download=true&access_token={access_token}"
                    embed = EMBED_TEMPLATE % {
                        "filename": info["name"],
                        "mimetype": info["mimetype"],
                        "downloadUrl": download_url,
                    }
                    attach_info += embed
            item.description = Markup(part_1 + attach_info + "</p>")
