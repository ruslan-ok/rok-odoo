from odoo import api, exceptions, fields, models, _


class FolderFavorite(models.Model):
    _name = "file.manager.folder.favorite"
    _description = "Favorite Folder"
    _order = "sequence ASC, id DESC"
    _rec_name = "folder_id"

    folder_id = fields.Many2one(
        "file.manager.folder", 
        "Folder",
        index=True, 
        required=True, 
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        "res.users", 
        "User", 
        index=True, 
        required=True, 
        ondelete="cascade",
    )
    sequence = fields.Integer(default=0)

    _sql_constraints = [
        ("unique_folder_user",
         "unique(folder_id, user_id)",
         "User already has this folder in favorites.")
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """ At creation, we need to set the max sequence, if not given, for each favorite to create, in order to keep
        a correct ordering as much as possible. Some sequence could be given in create values, that could lead to
        duplicated sequence per user_id. That is not an issue as they will be resequenced the next time the user reorder
        their favorites. """
        default_sequence = 1
        if any(not vals.get("sequence") for vals in vals_list):
            favorite = self.env["file.manager.folder.favorite"].search(
                [("user_id", "=", self.env.uid)],
                order="sequence DESC",
                limit=1
            )
            default_sequence = favorite.sequence + 1 if favorite else default_sequence
        for vals in vals_list:
            if not vals.get("sequence"):
                vals["sequence"] = default_sequence
                default_sequence += 1
        return super().create(vals_list)

    def write(self, vals):
        """ Whatever rights, avoid any attempt at privilege escalation. """
        if ("folder_id" in vals or "user_id" in vals) and not self.env.is_admin():
            raise exceptions.AccessError(_("Can not update the folder or user of a favorite."))
        return super().write(vals)

    def resequence_favorites(self, folder_ids):
        # Some folder may not be accessible by the user anymore. Therefore,
        # to prevent an access error, one will only resequence the favorites
        # related to the folders accessible by the user
        sequence = 0
        # Keep the same order as in folder_ids
        for folder_id in folder_ids:
            self.search([("folder_id", "=", folder_id), ("user_id", "=", self.env.uid)]).write({"sequence": sequence})
            sequence += 1
