from odoo import models, fields, _

class RokMigrationRoot(models.Model):
    _name = 'rok.migration.root'
    _description = 'Root Models to migrate'

    model_id = fields.Many2one(string='Model ID', comodel_name='ir.model')
    model = fields.Char(string='Model', related='model_id.model')
    name = fields.Char(string='Description', related='model_id.name')
    loaded_count = fields.Integer(string='Loaded Count', compute='_compute_count')
    migrated_count = fields.Integer(string='Migrated Count', compute='_compute_count')

    def _compute_count(self):
        for record in self:
            record.loaded_count = self.env["rok.migration.data"].search_count([("model", "=", record.model)])
            record.migrated_count = self.env["rok.migration.data"].search_count([("model", "=", record.model), ("target_id", "!=", False)])

    def action_delete_all(self):
        self.env["rok.migration.data"].delete_all()

    def action_delete_migrated_items(self):
        models = self.mapped("model")
        self.env["rok.migration.data"].delete_migrated_items(models)

    def action_load(self):
        relations = self.get_relations_for_root()
        self.env["rok.migration.data"].load_data(relations)

    def action_migrate(self):
        for model in self:
            model.migrate_model()

    def get_relations_for_root(self):
        root_models = self.search([]).mapped("model")
        relations = []
        self.scan_relations(root_models, relations)
        return relations

    def scan_relations(self, models_to_scan, relations_to_load):
        to_scan_child = []
        for model in models_to_scan:
            model_relation = model.replace(".", "_")
            if model_relation in relations_to_load:
                continue
            Model = self.env[model]
            fields = Model.fields_get(attributes=['type', 'relation_field', 'relation', 'relation_table'])
            child_models = [x.get("relation") for x in fields.values() if x.get("relation") and not x.get("relation").startswith("ir.")]
            child_models = list(set(child_models))
            for child_model in child_models:
                child_model_relation = child_model.replace(".", "_")
                if child_model_relation not in relations_to_load and child_model not in models_to_scan and child_model not in to_scan_child:
                    to_scan_child.append(child_model)
            relations_to_load.append(model_relation)
            m2m = [k for k,v in fields.items() if v["type"] == "many2many"]
            m2m_relations = [self.env[model]._fields[x].relation for x in m2m]
            for m2m_relation in m2m_relations:
                if m2m_relation:
                    relations_to_load.append(m2m_relation)
        if to_scan_child:
            self.scan_relations(to_scan_child, relations_to_load)

    def migrate_model(self):
        self.ensure_one()
        self.env["rok.migration.data"].migrate_model(self.model)
