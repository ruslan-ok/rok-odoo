/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DocumentsSearchPanel } from "@documents/views/search/documents_search_panel";

patch(DocumentsSearchPanel, {
    // Rok todo: check
    rootIcons: {
        ...DocumentsSearchPanel.rootIcons,
        SERVER_FOLDER: "fa-star",
    },
});