/** @odoo-module **/

import { formatDateTime } from '@web/core/l10n/dates';
import { registry } from '@web/core/registry';
import { standardWidgetProps } from '@web/views/widgets/standard_widget_props';
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useEffect, useRef, useState } from '@odoo/owl';
import FileManagerHierarchy from '@file_manager/components/hierarchy/hierarchy';
import MoveFolderDialog from '@file_manager/components/move_folder_dialog/move_folder_dialog';
import { FileUploader } from "@web/views/fields/file_handler";

class FileManagerTopbar extends Component {
    static template = "file_manager.FileManagerTopbar";
    static props = {
        ...standardWidgetProps,
    };
    static components = {
        FileManagerHierarchy,
        FileUploader,
    };

    setup() {
        super.setup();
        this.actionService = useService('action');
        this.dialog = useService('dialog');
        this.orm = useService('orm');
        this.uiService = useService('ui');

        this.buttonSharePanel = useRef('sharePanel_button');
        this.optionsBtn = useRef('optionsBtn');

        this.formatDateTime = formatDateTime;

        this.state = useState({
            displayChatter: false,
            displayHistory: false,
            displayPropertyPanel: !this.folderPropertiesIsEmpty,
            addingProperty: false,
            displaySharePanel: false,
        });

        onWillStart(async () => {
            this.isInternalUser = await user.hasGroup('base.group_user');
        });

        useEffect((optionsBtn) => {
            // Refresh "last edited" and "create date" when opening the options panel
            if (optionsBtn) {
                optionsBtn.addEventListener(
                    'shown.bs.dropdown',
                    () => this._setDates()
                );
            }
        }, () => [this.optionsBtn.el]);
    }

    get addFavoriteLabel(){
        return _t("Add to favorites");
    }

    get removeFavoriteLabel(){
        return _t("Remove from favorites");
    }

    _setDates() {
        if (this.props.record.data.create_date && this.props.record.data.last_edition_date) {
            this.state.createDate = this.props.record.data.create_date.toRelative();
            this.state.editionDate = this.props.record.data.last_edition_date.toRelative();
        }
    }

    /**
     * Show the Dialog allowing to move the current folder.
     */
    async onMoveFolderClick() {
        await this.env._saveIfDirty();
        this.dialog.add(MoveFolderDialog, {fileManagerFolder: this.props.record});
    }

    async onFileUploaded(file) {
        const att_data = {
            name: file.name,
            mimetype: file.type,
            datas: file.data,
            folder_id: this.props.record.resId,
        };
        await this.orm.create("file.manager.file", [att_data]);
    }
}

export const fileManagerTopbar = {
    component: FileManagerTopbar,
    fieldDependencies: [
        { name: "create_uid", type: "many2one", relation: "res.users" },
        { name: "display_name", type: "char" },
        { name: "parent_path", type: "char" },
        { name: "root_folder_id", type: "many2one", relation: "file_manager.file_manager_folder" },
    ],
};

registry.category('view_widgets').add('file_manager_topbar', fileManagerTopbar);
