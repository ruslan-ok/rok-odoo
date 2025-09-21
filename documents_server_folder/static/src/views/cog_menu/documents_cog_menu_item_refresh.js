import { STATIC_COG_GROUP_ACTION_BASIC } from "@documents/views/cog_menu/documents_cog_menu_group";
import { DocumentsCogMenuItem } from "@documents/views/cog_menu/documents_cog_menu_item";
import { _t } from "@web/core/l10n/translation";

export class DocumentsCogMenuItemRefresh extends DocumentsCogMenuItem {
    setup() {
        this.icon = "fa-refresh";
        this.label = _t("Refresh");
        super.setup();
    }

    // Rok todo: check
    async refreshServerFolder(resIds) {
        const action = await this.env.model.orm.call(
            "documents.document",
            "refresh_server_folder",
            [resIds]
        );
        if (action && Object.keys(action).length !== 0) {
            this.env.model.action.doAction(action);
        }
    }

    // Rok todo: check
    async doActionOnFolder(folder) {
        await this.refreshServerFolder(folder.id);
        await this.reload();
    }
}

// Rok todo: check
export const documentsCogMenuItemRefresh = {
    Component: DocumentsCogMenuItemRefresh,
    groupNumber: STATIC_COG_GROUP_ACTION_BASIC,
    isDisplayed: (env) =>
        DocumentsCogMenuItem.isVisible(env, ({ folder, documentService }) =>
            folder.rootId === "SERVER_FOLDER"
        ),
};
