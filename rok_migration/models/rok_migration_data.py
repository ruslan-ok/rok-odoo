import dotenv
import json
import os
import psycopg2
import logging
import datetime

_logger = logging.getLogger(__name__)

from odoo import models, fields, _
from odoo.models import LOG_ACCESS_COLUMNS
from odoo import Command, api

LOOKUPS = {
    "res.company": "id",
    "res.country": "code",
    "res.country.state": "code",
    "res.currency": "name",
    "res.user": "login",
}

class RokMigrationData(models.Model):
    _name = 'rok.migration.data'
    _description = 'Rok Migration Data  '

    model = fields.Char(string='Model')
    source_id = fields.Integer(string='Source ID', help='Original ID from source database')
    search_key = fields.Char(string='Search Key')
    data = fields.Json(string='Data', help='Data from source database')
    target_id = fields.Integer(string='Target ID', help='Target ID in target database')

    def clear_data(self, models):
        migration_data = self.search([("model", "in", models)])
        migrated_models = set(migration_data.mapped("model"))
        for model in migrated_models:
            migrated_data = self.search([("model", "=", model), ("target_id", "!=", False)])
            migrated_data_ids = migrated_data.mapped("target_id")
            migrated_items = self.env[model].browse(migrated_data_ids)
            migrated_items.unlink()
            migrated_data.write({"target_id": False})

        migration_data.unlink()

    def load_data(self, models):
        conn = self.get_source_connection()
        try:
            with conn.cursor() as cr:
                for model in models:
                    if self.search_count([("model", "=", model)]):
                        continue
                    self.load_model_data(model, cr)
        finally:
            conn.close()
        _logger.info("Loading data from source database: end")

    def get_source_connection(self):
        """Get connection to source database"""
        dotenv.load_dotenv()
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                connect_timeout=5,
            )
            return conn
        except Exception as e:
            _logger.error("Database connection error: %s", e)
            raise e

    def load_model_data(self, model, cr):
        _logger.info("Loading data for the model %s ...", model)
        table_name = "ir_act_report_xml" if model == "ir.actions.report" else model.replace(".", "_")
        cr.execute(f"SELECT COUNT(1) FROM information_schema.tables WHERE table_name = '{table_name}' AND table_schema = 'public'")
        if cr.fetchone()[0] == 0:
            _logger.warning("Table %s does not exist", table_name)
            return
        cr.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cr.description]
        rows = cr.fetchall()
        for row in rows:
            data = dict(zip(columns, row))
            fields_to_remove = [field for field in LOG_ACCESS_COLUMNS if field in data]
            for field, value in data.items():
                if isinstance(value, datetime.datetime):
                    data[field] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, datetime.date):
                    data[field] = value.strftime("%Y-%m-%d")
                elif type(data[field]).__name__ == "memoryview":
                    fields_to_remove.append(field)
            for field in fields_to_remove:
                del data[field]
            try:
                self.env["rok.migration.data"].create({
                    "model": model,
                    "source_id": data.get("id"),
                    "search_key": "",
                    "data": data
                })
            except Exception as e:
                _logger.warning("Could not create rok.migration.data for %s: %s", model, e)
                raise e
        _logger.info("Loading data from model %s: end", model)

    @api.model
    def get_many2one(self, relation, source_id):
        if isinstance(source_id, dict):
            source_id = int(list(source_id.keys())[0])
        migration_rec = self.env["rok.migration.data"].search([("model", "=", relation), ("source_id", "=", source_id)])
        lookup_key = LOOKUPS.get(relation)
        if lookup_key:
            item = self.env[relation].with_context(active_test=False).search([(lookup_key, "=", migration_rec.data.get(lookup_key))])
            if item and migration_rec.data.get("active"):
                item.active = True
            return item.id if item else False
        return migration_rec.migrate_one()

    def get_one2many(self, relation, relation_field, source_id):
        migration_recs = self.env["rok.migration.data"].search([("model", "=", relation), (relation_field, "=", source_id)])
        return Command.Set(migration_recs.mapped("target_id"))

    def get_many2many(self, relation, source_id):
        return Command.Set([])

    def get_model_fields_info(self, model):
        return self.env[model].fields_get(
            attributes=[
                'type', 'string', 'required', 'relation_field', 'default_export_compatible',
                'relation', 'definition_record', 'definition_record_field', 'exportable', 'readonly',
            ],
        )

    def migrate_model(self, model):
        _logger.info("Migrating model %s: start", model)
        actual_fields = self.get_model_fields_info(model)
        records = self.env["rok.migration.data"].search([("model", "=", model)])
        for record in records:
            record.migrate_one(actual_fields, fix_in_log=True)
        _logger.info("Migrating model %s: end", model)

    def migrate_one(self, actual_fields=None, fix_in_log=False):
        self.ensure_one()
        if self.target_id:
            item = self.env[self.model].browse(self.target_id)
            if item:
                return self.target_id
            else:
                raise ValueError("DEBUG: Target ID %s for model %s does not exist", self.target_id, self.model)
                # self.write({"target_id": False})
        if not self.sanity_check():
            _logger.warning("Sanity check failed for model %s, record %s", self.model, self.source_id)
            return False
        if not actual_fields:
            actual_fields = self.get_model_fields_info(self.model)
        item_vals = {}
        for actual_field, actual_field_info in actual_fields.items():
            if actual_field == "id" or not self.data.get(actual_field):
                continue
            match actual_field_info.get("type"):
                case "many2one":
                    relation = actual_field_info.get("relation")
                    source_id = self.data[actual_field]
                    if relation == self.model and source_id == self.data.get("id"):
                        continue
                    item_vals[actual_field] = self.get_many2one(relation, source_id)
                case "one2many":
                    relation = actual_field_info.get("relation")
                    relation_field = actual_field_info.get("relation_field")
                    item_vals[actual_field] = self.get_one2many(relation, relation_field, self.source_id)
                case "many2many":
                    relation = actual_field_info.get("relation")
                    item_vals[actual_field] = self.get_many2many(relation, self.source_id)
                case "selection":
                    value = self.data[actual_field]
                    field_def = self.env["ir.model.fields"].search([("model", "=", self.model), ("name", "=", actual_field)])
                    keys = field_def.selection_ids.mapped("value")
                    if keys and value not in keys:
                        value = keys[0]
                    item_vals[actual_field] = value
                case _:
                    value = self.integrity_transform(actual_field, self.data[actual_field])
                    if isinstance(value, dict):
                        value = self._fetch_from_json(value)
                    item_vals[actual_field] = value
        new_item = self.env[self.model].create(item_vals)
        self.write({"target_id": new_item.id})
        if fix_in_log:
            _logger.info("Migrated record %s: %s", self.model, new_item.get("name", new_item.get("id")))
        return new_item.id

    def _fetch_from_json(self, json_data, extra_key=None):
        if not json_data:
            return False
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        return json_data.get("en_US", json_data.get("en_GB", json_data.get(extra_key, False)))

    def sanity_check(self):
        if self.model == "res.partner":
            return bool(self.data.get("name"))
        return True

    def integrity_transform(self, field, value):
        if self.model == "res.partner" and field == "peppol_endpoint":
            if value == "PL: NIP 526-00-03-819":
                return "PL5260003819"
        return value