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
        models = self.get_models_for_root()
        self.env["rok.migration.data"].load_data(models)

    def action_migrate(self):
        for model in self:
            model.migrate_model()

    def get_models_for_root(self):
        models = [model.model for model in self]
        relations = []
        self.scan_relations(models, relations)
        return relations

    def scan_relations(self, to_scan, done):
        to_scan_child = []
        for model in to_scan:
            if model in done:
                continue
            Model = self.env[model]
            fields = Model.fields_get(
                attributes=[
                    'type', 'string', 'required', 'relation_field', 'default_export_compatible',
                    'relation', 'definition_record', 'definition_record_field', 'exportable', 'readonly',
                ],
            )
            child_relations = [x.get("relation") for x in fields.values() if x.get("relation") and not x.get("relation").startswith("ir.")]
            child_relations = list(set(child_relations))
            for relation in child_relations:
                if relation not in done and relation not in to_scan and relation not in to_scan_child:
                    to_scan_child.append(relation)
            done.append(model)
        if to_scan_child:
            self.scan_relations(to_scan_child, done)

    def migrate_model(self):
        self.ensure_one()
        self.env["rok.migration.data"].migrate_model(self.model)
