/** @odoo-module */

import { FileManagerSidebarRow } from "./sidebar_row";
import { user } from "@web/core/user";

import { Component, onWillStart, useChildSubEnv } from "@odoo/owl";

/**
 * This file defines the different sections used in the sidebar.
 * Each section is responsible of displaying an array of root folders and
 * their children.
 */

export class FileManagerSidebarSection extends Component {
    static template = "";
    static props = {
        rootIds: Array,
        unfoldedIds: Set,
        record: Object,
    };
    static components = {
        FileManagerSidebarRow,
    };

    setup() {
        super.setup();
        onWillStart(async () => {
            this.isInternalUser = await user.hasGroup('base.group_user');
        });
    }
}

export class FileManagerSidebarFavoriteSection extends FileManagerSidebarSection {
    static template = "file_manager.SidebarFavoriteSection";
    
    setup() {
        super.setup();

        // (Un)fold in the favorite tree by default.
        useChildSubEnv({
            fold: id => this.env.fold(id, true),
            unfold: id => this.env.unfold(id, true),
        });
    }
}

export class FileManagerSidebarPrivateSection extends FileManagerSidebarSection {
    static template = "file_manager.SidebarPrivateSection";

    createRoot() {
        this.env.createFolder();
    }
}
