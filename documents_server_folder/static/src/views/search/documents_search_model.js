/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DocumentsSearchModel } from "@documents/views/search/documents_search_model";
import { browser } from "@web/core/browser/browser";

patch(DocumentsSearchModel.prototype, {
    _ensureCategoryValue(category, valueIds) {
        if (
            valueIds.includes(category.activeValueId) &&
            this._isCategoryValueReachable(category, category.activeValueId)
        ) {
            return;
        }

        // If not set in context, or set to an unknown value, set active value
        // from localStorage
        const storageItem = browser.localStorage.getItem("searchpanel_documents_document");
        category.activeValueId =
            storageItem && !["COMPANY", "MY", "SERVER_FOLDER", "RECENT", "SHARED", "TRASH"].includes(storageItem)
                ? JSON.parse(storageItem)
                : storageItem;
        if (
            ["COMPANY", "MY", "SERVER_FOLDER", "RECENT", "SHARED", "TRASH"].includes(category.activeValueId)
            || (valueIds.includes(category.activeValueId)
                && this._isCategoryValueReachable(category, category.activeValueId))
        ) {
            return;
        }
        // valueIds might contain different values than category.values
        if (category.values.has(category.activeValueId)) {
            // We might be in a deleted subfolder, try to find the parent.
            let newSection = category.values.get(
                category.values.get(category.activeValueId).parentId
            );
            while (newSection && !this._isCategoryValueReachable(category, newSection.id)) {
                newSection = category.values.get(newSection.parentId);
            }
            if (newSection) {
                category.activeValueId = newSection.id || valueIds[Number(valueIds.length > 1)];
            } else {
                category.activeValueId = this.documentService.userIsInternal ? "COMPANY" : valueIds[0];
            }
            browser.localStorage.setItem("searchpanel_documents_document", category.activeValueId);
        } else {
            // If still not a valid value, default to All (id=false) for internal users
            // or root folder for portal users
            category.activeValueId = this.documentService.userIsInternal ? false : valueIds[0];
        }
    },
});