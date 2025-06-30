from werkzeug.exceptions import BadRequest
from odoo import fields, http, _
from odoo.exceptions import MissingError
from odoo.http import request
from odoo.tools import replace_exceptions, consteq


class ShareRoute(http.Controller):

    @classmethod
    def _from_access_token(cls, access_token, *, skip_log=False, follow_shortcut=False):
        Doc = request.env["file.manager.file"]

        # Document record
        try:
            document_token, __, encoded_id = access_token.rpartition("o")
            document_id = int(encoded_id, 16)
        except ValueError:
            return Doc
        if not document_token or document_id < 1:
            return Doc
        document_sudo = Doc.browse(document_id).sudo()
        try:
            if not document_sudo.document_token: # like exists() but prefetch 
                return Doc
        except MissingError:
            return Doc

        # Permissions
        if not (consteq(document_token, document_sudo.document_token)):
            return Doc
        if not request.env.user._is_internal() and not document_sudo.active:
            return Doc

        # Document access
        skip_log = skip_log or request.env.user._is_public()
        if not skip_log:
            for doc_sudo in filter(bool, (document_sudo, document_sudo.shortcut_document_id)):
                if access := request.env["documents.access"].sudo().search([
                    ("partner_id", "=", request.env.user.partner_id.id),
                    ("document_id", "=", doc_sudo.id),
                ]):
                    access.last_access_date = fields.Datetime.now()
                else:
                    request.env["documents.access"].sudo().create([{
                        "document_id": doc_sudo.id,
                        "partner_id": request.env.user.partner_id.id,
                        "last_access_date": fields.Datetime.now(),
                    }])

        # Shortcut
        if follow_shortcut:
            if target_sudo := document_sudo.shortcut_document_id:
                if (target_sudo.user_permission != "none"
                    or (target_sudo.access_via_link != "none"
                        and not target_sudo.is_access_via_link_hidden)):
                    document_sudo = target_sudo
                else:
                    document_sudo = Doc

        # Extra validation step, to run with the target
        if (
            request.env.user._is_public()
            and document_sudo.type == "binary"
            and not document_sudo.attachment_id
            and document_sudo.access_via_link != "edit"
        ):
            # public cannot access a document request, unless access_via_link="edit"
            return Doc

        return document_sudo

    @http.route(["/file_manager/thumbnail/<access_token>",
                 "/file_manager/thumbnail/<access_token>/<int:width>x<int:height>"],
                type="http", auth="public", readonly=True)
    def documents_thumbnail(self, access_token, width="0", height="0", unique=""):
        with replace_exceptions(ValueError, by=BadRequest):
            width = int(width)
            height = int(height)
        send_file_kwargs = {}
        if unique:
            send_file_kwargs["immutable"] = True
            send_file_kwargs["max_age"] = http.STATIC_CACHE_LONG
        document_sudo = self._from_access_token(access_token, skip_log=True)
        return request.env["ir.binary"]._get_image_stream_from(
            document_sudo, "thumbnail", width=width, height=height
        ).get_response(as_attachment=False, **send_file_kwargs)

