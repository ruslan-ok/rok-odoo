/** @odoo-module */

import FilestoreIcon from "@rok_filestore_qweb/components/filestore_icon/filestore_icon";
import { useService } from "@web/core/utils/hooks";

import { Component, onWillUpdateProps, useState } from "@odoo/owl";

/**
 * The SidebarRow component is responsible of displaying an folder (and its
 * children recursively) in a section of the sidebar, and modifying the record
 * of the folder (such as updating the icon).
 */

class FilestoreSidebarIcon extends  FilestoreIcon {
    static props = {
        folder: Object,
        readonly: Boolean,
        record: Object,
        iconClasses: {type: String, optional: true},
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
    }

    get icon() {
        return this.props.folder.icon || '📄';
    }

    async updateIcon(icon) {
        if (this.props.record.resId === this.props.folder.id) {
            this.props.record.update({ icon });
        } else {
            await this.orm.write(
                "rok_filestore_qweb.rok_ilestore_folder",
                [this.props.folder.id],
                {icon}
            );
            this.props.folder.icon = icon;
        }
    }
}

export class FilestoreSidebarRow extends Component {
    static props = {
        folder: Object,
        unfolded: Boolean,
        unfoldedIds: Set,
        record: Object,
    };
    static template = "rok_filestore_qweb.SidebarRow";
    static components = {
        FilestoreSidebarIcon,
        FilestoreSidebarRow
    };

    setup() {
        super.setup();
        this.orm = useService("orm");

        this.state = useState({
            unfolded: false,
        });

        onWillUpdateProps(nextProps => {
            // Remove the loading spinner when the folder is rendered as
            // being unfolded
            if (this.state.loading && nextProps.unfolded === true) {
                this.state.loading = false;
            }
        });
    }

    get hasChildren() {
        return this.props.folder.has_children;
    }

    get isActive() {
        return this.props.record.resId === this.props.folder.id;
    }

    get isLocked() {
        return this.props.folder.is_locked;
    }

    get isReadonly() {
        // return !this.props.folder.user_can_write;
        return false;
    }

    /**
     * Create a new child folder for the row's folder.
     */
    createChild() {
        this.env.createFolder(this.props.folder.category, this.props.folder.id);
    }

    /**
     * (Un)fold the row
     */
    onCaretClick() {
        if (!this.props.folder.has_children) {
            return;
        }
        if (this.props.unfolded) {
            this.env.fold(this.props.folder.id);
        } else if (!this.state.loading) {
            this.state.loading = true;
            // If there are a lot of folders, make sure the rendering caused
            // by the state change and the one cause by the prop update are not
            // done at once, because otherwise the loader will not be shown.
            // If there are not too much folders, the renderings can be done
            // at once so that there is no flickering.
            if (this.props.folder.child_ids.length > 500) {
                setTimeout(() => this.env.unfold(this.props.folder.id), 0);
            } else {
                this.env.unfold(this.props.folder.id);
            }
        }
    }

    /**
     * Open the row's folder
     */
    onNameClick() {
        this.env.openFolder(this.props.folder.id);
    }
}
