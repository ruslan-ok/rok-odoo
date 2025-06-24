/** @odoo-module */

import { FilestoreSidebarRow } from "./sidebar_row";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";

import { Component, onWillStart, useChildSubEnv } from "@odoo/owl";

/**
 * This file defines the different sections used in the sidebar.
 * Each section is responsible of displaying an array of root folders and
 * their children.
 */

export class FilestoreSidebarSection extends Component {
    static template = "";
    static props = {
        rootIds: Array,
        unfoldedIds: Set,
        record: Object,
    };
    static components = {
        FilestoreSidebarRow,
    };

    setup() {
        super.setup();
        onWillStart(async () => {
            this.isInternalUser = await user.hasGroup('base.group_user');
        });
    }
}

export class FilestoreSidebarFavoriteSection extends FilestoreSidebarSection {
    static template = "rok_filestore_qweb.SidebarFavoriteSection";
    
    setup() {
        super.setup();

        // (Un)fold in the favorite tree by default.
        useChildSubEnv({
            fold: id => this.env.fold(id, true),
            unfold: id => this.env.unfold(id, true),
        });
    }
}

export class FilestoreSidebarWorkspaceSection extends FilestoreSidebarSection {
    static template = "rok_filestore_qweb.SidebarWorkspaceSection";
    
    setup() {
        super.setup();
        this.command = useService("command");
    }

    createRoot() {
        this.env.createFolder("workspace");
    }

    searchHiddenFolder() {
        this.command.openMainPalette({searchValue: "$"});
    }
}

export class FilestoreSidebarSharedSection extends FilestoreSidebarSection {
    static template = "rok_filestore_qweb.SidebarSharedSection";
}

export class FilestoreSidebarPrivateSection extends FilestoreSidebarSection {
    static template = "rok_filestore_qweb.SidebarPrivateSection";

    createRoot() {
        this.env.createFolder("private");
    }
}
