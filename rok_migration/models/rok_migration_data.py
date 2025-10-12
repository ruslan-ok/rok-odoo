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

class RokMigrationData(models.Model):
    _name = 'rok.migration.data'
    _description = 'Rok Migration Data  '

    model = fields.Char(string='Model')
    relation = fields.Char(string='Relation (Table)')
    source_id = fields.Integer(string='Source ID', help='Original ID from source database')
    data = fields.Json(string='Data', help='Data from source database')
    target_id = fields.Integer(string='Target ID', help='Target ID in target database')

    def delete_all(self):
        models = self.search([("target_id", "!=", False)]).mapped("model")
        self.delete_migrated_items(models)
        self.search([]).unlink()

    def delete_migrated_items(self, models):
        migration_data = self.search([("model", "in", models), ("target_id", "!=", False)])
        migrated_models = set(migration_data.mapped("model"))
        for model in migrated_models:
            migrated_data = self.search([("model", "=", model), ("target_id", "!=", False)])
            migrated_data_ids = migrated_data.mapped("target_id")
            migrated_items = self.env[model].browse(migrated_data_ids)
            migrated_items.unlink()
            migrated_data.write({"target_id": False})

        migration_data.unlink()

    def load_data(self, relations):
        relation_model_map = {}
        for model_name, model in self.env.items():
            table_name = getattr(model, '_table', None)
            if table_name and table_name in relations:
                relation_model_map[table_name] = model_name
        conn = self.get_source_connection()
        try:
            with conn.cursor() as cr:
                for relation in relations:
                    if self.search_count([("relation", "=", relation)]):
                        continue
                    self.load_relation_data(relation, relation_model_map.get(relation), cr)
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

    def load_relation_data(self, relation, model, cr):
        _logger.info("Loading data for the relation %s ...", relation)
        cr.execute(f"SELECT COUNT(1) FROM information_schema.tables WHERE table_name = '{relation}' AND table_schema = 'public'")
        if cr.fetchone()[0] == 0:
            _logger.warning("Table %s does not exist", relation)
            return
        cr.execute(f"SELECT * FROM {relation}")
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
                    "data": data
                })
            except Exception as e:
                _logger.warning("Could not create rok.migration.data for %s: %s", model, e)
                raise e
        _logger.info("Loading data from relation %s: end", relation)

    @api.model
    def get_many2one(self, owner, relation, source_id):
        if isinstance(source_id, dict):
            source_id = int(list(source_id.keys())[0])
        migration_rec = self.env["rok.migration.data"].search([("model", "=", relation), ("source_id", "=", source_id)])
        LOOKUPS = {
            "res.company": "id",
            "res.country": "code",
            "res.country.state": "code",
            "res.currency": "name",
            "res.users": "login",
        }
        lookup_key = LOOKUPS.get(relation)
        if lookup_key:
            item = self.env[relation].with_context(active_test=False).search([(lookup_key, "=", migration_rec.data.get(lookup_key))])
            if item and migration_rec.data.get("active"):
                item.active = True
            return item.id if item else False
        if len(migration_rec) != 1:
            raise ValueError("DEBUG: Multiple records found for model %s, source_id %s", relation, source_id)
        return migration_rec.migrate_one(owner)

    def get_one2many(self, owner, source_id, field_name):
        o2m_field_def = self.env["ir.model.fields"].search([("model", "=", self.model), ("name", "=", field_name)])
        related_model = o2m_field_def.relation
        relation_field = o2m_field_def.relation_field
        migration_recs = self.env["rok.migration.data"].search([("model", "=", related_model)])
        FILTER_MAP = {
            "res.partner": {
                "message_follower_ids": lambda x: x.data.get("res_model") == self.model and x.data.get(relation_field) == source_id,
                "message_ids": lambda x: x.data.get("model") == self.model and x.data.get(relation_field) == source_id,
            },
        }
        filter_func = FILTER_MAP.get(self.model, {}).get(field_name)
        if filter_func:
            migration_recs = migration_recs.filtered(filter_func)
        else:
            migration_recs = migration_recs.filtered(lambda x: x.data.get(relation_field) == source_id)
        ids_to_link = []
        for rec in migration_recs:
            if rec.data.get(relation_field) == source_id:
                new_id = rec.migrate_one(owner)
                if new_id:
                    ids_to_link.append(new_id)
        return Command.set(ids_to_link) if ids_to_link else False

    def get_many2many(self, owner, source_id, field_name):
        m2m_field_def = self.env["ir.model.fields"].search([("model", "=", self.model), ("name", "=", field_name)])
        relation_table = m2m_field_def.relation_table
        column1 = m2m_field_def.column1
        column2 = m2m_field_def.column2
        related_model = m2m_field_def.relation
        ids_to_link = []
        if relation_table:
            migration_recs = self.env["rok.migration.data"].search([("relation", "=", relation_table)])
            for rec in migration_recs:
                if rec.data.get(column1) == source_id:
                    item_data = self.env["rok.migration.data"].search([("model", "=", related_model), ("source_id", "=", rec.data.get(column2))])
                    new_id = item_data.migrate_one(owner)
                    if new_id:
                        ids_to_link.append(new_id)
        return Command.set(ids_to_link) if ids_to_link else False

    def get_model_fields_info(self, model):
        return self.env[model].fields_get(attributes=['type', 'comodel_name', 'base_field', 'relation_field', 'relation', 'relation_table', 'related_field', 'inverse', 'inverse_name', 'model_name', 'compute'])

    def migrate_model(self, model):
        _logger.info("Migrating model %s: start", model)
        dotenv.load_dotenv()
        owner_name = os.getenv("APP_OWNER_NAME")
        owner = self.env["res.users"].search([("login", "=", owner_name)], limit=1)
        actual_fields = self.get_model_fields_info(model)
        records = self.env["rok.migration.data"].search([("model", "=", model)])
        for record in records:
            record.migrate_one(owner, actual_fields, fix_in_log=True)
        _logger.info("Migrating model %s: end", model)

    def migrate_one(self, owner, actual_fields=None, fix_in_log=False):
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
            relation = actual_field_info.get("relation")
            field_type = actual_field_info.get("type")
            if actual_field == "id" or (not self.data.get(actual_field) and not relation and field_type != "boolean"):
                continue
            match actual_field_info.get("type"):
                case "many2one":
                    source_id = self.data.get(actual_field)
                    if not source_id:
                        continue
                    if relation == self.model and source_id == self.data.get("id"):
                        continue
                    item_vals[actual_field] = self.get_many2one(owner, relation, source_id)
                case "one2many":
                    continue
                    # source_id = self.source_id
                    # value = self.get_one2many(owner, source_id, actual_field)
                    # if not value:
                    #     continue
                    # item_vals[actual_field] = value
                case "many2many":
                    continue
                    # source_id = self.source_id
                    # value = self.get_many2many(owner, source_id, actual_field)
                    # if not value:
                    #     continue
                    # item_vals[actual_field] = value
                case "selection":
                    value = self.data[actual_field]
                    field_def = self.env["ir.model.fields"].search([("model", "=", self.model), ("name", "=", actual_field)])
                    keys = field_def.selection_ids.mapped("value")
                    if keys and value not in keys:
                        value = keys[0]
                    item_vals[actual_field] = value
                case _:
                    value = self.integrity_transform(actual_field, self.data.get(actual_field))
                    if isinstance(value, dict):
                        value = self._fetch_from_json(value)
                    item_vals[actual_field] = value
        if self.model == "knowledge.article":
            if not item_vals.get("parent_id"):
                item_vals["article_member_ids"] = [Command.create({
                    "partner_id": owner.partner_id.id,
                    "permission": "write",
                })]
        new_item = self.env[self.model].create(item_vals)
        self.write({"target_id": new_item.id})
        if fix_in_log:
            _logger.info("Migrated record %s: %s", self.model, new_item.name if self.model in ["res.partner", "knowledge.article"] else new_item.id)
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
        match self.model:
            case "res.partner":
                if field == "peppol_endpoint":
                    if value == "PL: NIP 526-00-03-819":
                        return "PL5260003819"
            case "knowledge.article":
                if field == "parent_path":
                    return False
        return value