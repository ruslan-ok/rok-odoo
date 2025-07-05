/** @odoo-module **/

import { registry } from "@web/core/registry";

import { DocumentsActivityView } from "@documents/views/activity/documents_activity_view";
import { DocumentsServerFolderSearchModel } from "../search/documents_search_model";

export const DocumentsServerFolderActivityView = {
    ...DocumentsActivityView,
    SearchModel: DocumentsServerFolderSearchModel,
};

registry.category("views").add("documents_server_folder_activity", DocumentsServerFolderActivityView);
