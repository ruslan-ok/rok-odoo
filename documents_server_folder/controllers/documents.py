import json
import os

from werkzeug.exceptions import BadRequest, Forbidden

from odoo import _, http
from odoo.http import request
from odoo.tools import replace_exceptions

from odoo.addons.documents.controllers.documents import ShareRoute

ERR_MISSING_FILES = "missing files"
ERR_MULTIPLE_FILES_INSIDE_DOC = "cannot save multiple files inside a single document"
ERR_ONLY_INTERNAL_USERS_CAN_UPLOAD_FILES = "only internal users can upload files"


class DsfShareRoute(ShareRoute):
    def _max_content_length(self):
        return request.env["documents.document"].get_document_max_upload_limit()

    @http.route(
        ["/documents/upload/", "/documents/upload/<access_token>"],
        type="http",
        auth="public",
        methods=["POST"],
        max_content_length=_max_content_length,
    )
    def documents_upload(
        self,
        ufile,
        access_token="",
        owner_id="",
        partner_id="",
        res_id="",
        res_model="",
        allowed_company_ids="",
    ):
        if allowed_company_ids:
            request.update_context(allowed_company_ids=json.loads(allowed_company_ids))
        is_internal_user = request.env.user._is_internal()
        if is_internal_user and not access_token:
            document_sudo = request.env["documents.document"].sudo()
        else:
            document_sudo = self._from_access_token(access_token)
            if (
                not document_sudo
                or (
                    document_sudo.user_permission != "edit"
                    and document_sudo.access_via_link != "edit"
                )
                or document_sudo.type not in ("binary", "folder")
            ):
                raise request.not_found()
        if not document_sudo.located_on_the_server:
            return super().documents_upload(
                ufile,
                access_token,
                owner_id,
                partner_id,
                res_id,
                res_model,
                allowed_company_ids,
            )

        files = request.httprequest.files.getlist("ufile")
        if not files:
            raise BadRequest(ERR_MISSING_FILES)
        if len(files) > 1 and document_sudo.type not in (False, "folder"):
            raise BadRequest(ERR_MULTIPLE_FILES_INSIDE_DOC)

        if is_internal_user:
            with replace_exceptions(ValueError, by=BadRequest):
                owner_id = int(owner_id) if owner_id else request.env.user.id
                partner_id = int(partner_id) if partner_id else False
                res_model = res_model or "documents.document"
                res_id = int(res_id) if res_id else False
        elif owner_id or partner_id or res_id or res_model:
            raise Forbidden(ERR_ONLY_INTERNAL_USERS_CAN_UPLOAD_FILES)
        else:
            owner_id = (
                document_sudo.owner_id.id
                if request.env.user.is_public
                else request.env.user.id
            )
            partner_id = False
            res_model = "documents.document"
            res_id = False  # replaced by the document's id

        document_ids = self._documents_upload_to_the_server(
            document_sudo,
            files,
            owner_id,
            partner_id,
            res_id,
            res_model,
        )
        if len(document_ids) == 1:
            document_sudo = document_sudo.browse(document_ids)

        if request.env.user._is_public():
            return request.redirect(document_sudo.access_url)
        return request.make_json_response(document_ids)

    def _documents_upload_to_the_server(
        self,
        document_sudo,
        files,
        owner_id,
        partner_id,
        res_id,
        res_model,
    ):
        """Replace an existing document or upload a new one."""

        document_ids = []
        if document_sudo.type == "binary":
            values = {"file": files[0]}
            self._documents_upload_to_the_server_create_write(document_sudo, values)
            document_ids.append(document_sudo.id)
        else:
            folder_sudo = document_sudo
            for file in files:
                document_sudo = self._documents_upload_to_the_server_create_write(
                    folder_sudo,
                    {
                        "file": file,
                        "type": "binary",
                        "access_via_link": "none"
                        if folder_sudo.access_via_link in (False, "none")
                        else "view",
                        "folder_id": folder_sudo.id,
                        "owner_id": owner_id,
                        "partner_id": partner_id,
                        "res_model": res_model,
                        "res_id": res_id,
                    },
                )
                document_ids.append(document_sudo.id)

            # Make sure uploader can access documents in "Company"
            document_sudo.filtered(
                lambda d: not d.folder_id
                and d.owner_id == request.env.ref("base.user_root"),
            ).action_update_access_rights(
                partners={request.env.user.partner_id: ("edit", False)},
            )

        return document_ids

    def _documents_upload_to_the_server_create_write(self, document_sudo, vals):
        """
        The actual function that either write vals on a binary document
        or create a new document with vals inside a folder document.
        """
        if document_sudo.type == "binary":
            path = document_sudo.get_full_path()
            with open(path, "wb") as f:
                f.write(vals["file"].read())
        else:
            folder_path = document_sudo.get_full_path()
            file_name = vals["file"].filename
            path = os.path.join(folder_path, file_name)
            path = os.path.normpath(os.path.normcase(path))
            with open(path, "wb") as f:
                f.write(vals["file"].read())
            document_sudo = document_sudo.create_file(
                document_sudo.id,
                folder_path,
                file_name,
            )

        if not document_sudo.res_model:
            document_sudo.res_model = "documents.document"
        if document_sudo.res_model == "documents.document" and not document_sudo.res_id:
            document_sudo.res_id = document_sudo.id
        if any(field_name in vals for field_name in ["raw", "datas", "attachment_id"]):
            document_sudo.message_post(
                body=_(
                    "Document uploaded by %(user)s",
                    user=request.env.user.name,
                ),
            )

        return document_sudo
