import { patch } from "@web/core/utils/patch";
import { DocumentsCogMenu } from "@documents/views/cog_menu/documents_cog_menu";
import { documentsCogMenuItemRefresh } from "./documents_cog_menu_item_refresh";


patch(DocumentsCogMenu.prototype, {
    async _registryItems() {
        let enabledItems = await super._registryItems();
        const item = documentsCogMenuItemRefresh;
        if (enabledItems && item && await item.isDisplayed(this.env)) {
            enabledItems.push({
                Component: item.Component,
                groupNumber: item.groupNumber,
                key: item.Component.name,
            });
        }
        return enabledItems;
    },
});