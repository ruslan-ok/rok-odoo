from odoo import models, fields

class RokFilestoreFile(models.TransientModel):
    _name = 'rok.filestore.file'
    _description = 'Represent file in filesystem'

    folder_id = fields.Many2one('rok.filestore.folder', "Folder")
    name = fields.Char("Name", required=True)
    file_size = fields.Integer("File Size (bytes)", default=0)
    mime_type = fields.Char("File Type", required=True)
