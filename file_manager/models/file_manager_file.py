import os
import base64
import mimetypes
import logging
from odoo import models, fields, api
from odoo.tools import image, str2bool
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FileManagerFile(models.TransientModel):
    _name = "file.manager.file"
    _description = "Represent file in filesystem"

    folder_id = fields.Many2one("file.manager.folder", "Folder")
    name = fields.Char("Name", required=True)
    file_size = fields.Integer("File Size (bytes)", default=0)
    mimetype = fields.Char("File Type", required=True)

    def _compute_mimetype(self, values):
        """ compute the mimetype of the given values
            :param values : dict of values to create or write an ir_attachment
            :return mime : string indicating the mimetype, or application/octet-stream by default
        """
        mimetype = None
        if values.get("mimetype"):
            mimetype = values["mimetype"]
        if not mimetype and values.get("name"):
            mimetype = mimetypes.guess_type(values["name"])[0]
        if not mimetype and values.get("url"):
            mimetype = mimetypes.guess_type(values["url"].split("?")[0])[0]
        if not mimetype or mimetype == "application/octet-stream":
            raw = None
            if values.get("raw"):
                raw = values["raw"]
            elif values.get("datas"):
                raw = base64.b64decode(values["datas"])
            if raw:
                mimetype = guess_mimetype(raw)
        return mimetype and mimetype.lower() or "application/octet-stream"

    def _postprocess_contents(self, values):
        ICP = self.env["ir.config_parameter"].sudo().get_param
        supported_subtype = ICP("base.image_autoresize_extensions", "png,jpeg,bmp,tiff").split(",")

        mimetype = values["mimetype"] = self._compute_mimetype(values)
        _type, _match, _subtype = mimetype.partition("/")
        is_image_resizable = _type == "image" and _subtype in supported_subtype
        if is_image_resizable and (values.get("datas") or values.get("raw")):
            is_raw = values.get("raw")

            # Can be set to 0 to skip the resize
            max_resolution = ICP("base.image_autoresize_max_px", "1920x1920")
            if str2bool(max_resolution, True):
                try:
                    if is_raw:
                        img = image.ImageProcess(values["raw"], verify_resolution=False)
                    else:  # datas
                        img = image.ImageProcess(base64.b64decode(values["datas"]), verify_resolution=False)

                    if not img.image:
                        _logger.info("Post processing ignored : Empty source, SVG, or WEBP")
                        return values

                    w, h = img.image.size
                    nw, nh = map(int, max_resolution.split("x"))
                    if w > nw or h > nh:
                        img = img.resize(nw, nh)
                        quality = int(ICP("base.image_autoresize_quality", 80))
                        image_data = img.image_quality(quality=quality)
                        if is_raw:
                            values["raw"] = image_data
                        else:
                            values["datas"] = base64.b64encode(image_data)
                except UserError as e:
                    # Catch error during test where we provide fake image
                    # raise UserError(_("This file could not be decoded as an image file. Please try with a different file."))
                    msg = str(e)  # the exception can be lazy-translated, resolve it here
                    _logger.info("Post processing ignored : %s", msg)
        return values

    def _check_contents(self, values):
        mimetype = values["mimetype"] = self._compute_mimetype(values)
        xml_like = "ht" in mimetype or ( # hta, html, xhtml, etc.
                "xml" in mimetype and    # other xml (svg, text/xml, etc)
                not mimetype.startswith("application/vnd.openxmlformats"))  # exception for Office formats
        force_text = xml_like and (
            self.env.context.get("attachments_mime_plainxml")
            or not self.env["ir.ui.view"].sudo(False).has_access("write")
        )
        if force_text:
            values["mimetype"] = "text/plain"
        if not self.env.context.get("image_no_postprocess"):
            values = self._postprocess_contents(values)
        return values

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if "folder_id" not in values:
                continue
            values = self._check_contents(values)
            raw, datas = values.pop("raw", None), values.pop("datas", None)
            if raw or datas:
                if isinstance(raw, str):
                    raw = raw.encode()
                file_data = raw or base64.b64decode(datas or b"")
                values["file_size"] = len(file_data)
                folder_id = values["folder_id"]
                del values["folder_id"]
                folder = self.env["file.manager.folder"].browse(folder_id)
                root_path = self.env.user.file_manager_path
                file_path = os.path.join(root_path, folder.path, values["name"])
                with open(file_path, "wb") as f:
                    f.write(file_data)
    
        return super().create(vals_list)

    def unlink(self):
        if self.env.context.get("remove_file"):
            root_path = self.env.user.file_manager_path
            for file in self:
                file_path = os.path.join(root_path, file.folder_id.path, file.name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        return super().unlink()