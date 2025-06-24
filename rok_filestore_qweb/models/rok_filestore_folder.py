from odoo import models, fields, _, api
# from odoo.exceptions import UserError

class RokFilestoreFolder(models.TransientModel):
    _name = 'rok.filestore.folder'
    _description = 'Represent folder in filesystem'

    path = fields.Char("Filestore Path")
    name = fields.Char("Name", required=True)
    parent_id = fields.Many2one('rok.filestore.folder', "Parent Folder", ondelete='cascade', index=True, required=False)
    child_ids = fields.One2many('rok.filestore.folder', 'parent_id', "Child Folders", copy=True, auto_join=True)
    file_ids = fields.One2many('rok.filestore.file', 'folder_id', "Files", copy=True, auto_join=True)

    @api.model
    def default_get(self, fields_list):
        """Populate the model with the root folder."""
        res = super().default_get(fields_list)
        res.update({
            'name': 'Root Folder',
            'path': '/',
            'parent_id': False,
        })
        return res

    def get_sidebar_folders(self, unfolded_ids=False):
        return {
            "folders": [],
            "favorite_ids": [],
            "active_folder_accessible_root_id": False,
        }
