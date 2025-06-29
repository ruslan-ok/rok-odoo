import { Dialog } from '@web/core/dialog/dialog';
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { SelectMenu } from '@web/core/select_menu/select_menu';

import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

class MoveFolderDialog extends Component {

    static template = "file_manager.MoveFolderDialog";
    static components = { Dialog, SelectMenu };
    static props = {
        close: Function,
        fileManagerFolder: Object
    };

    setup() {
        this.size = 'md';
        this.orm = useService("orm");
        this.state = useState({selectedParentFolder: false, selectionDisplayGroups: []});
        this.placeholderLabel = _t('Choose a Folder...');
        this.toggler = useRef("togglerRef");

        onWillStart(this.fetchValues);

        //autofocus
        useEffect((toggler) => {
            toggler.click();
        }, () => [this.toggler.el]);

    }

    /**
     * For this dialog we needed to get valid folders since the user can move a
     * folder either under a specific folder, that becomes its parent.
     *
     * @param {String} searchValue Term inputted by the user in the SelectMenu's input
     */
    async fetchValues(searchValue) {
        const fileManagerFolders = await this.orm.call(
            'file_manager.file_manager_folder',
            'get_valid_parent_options',
            [this.props.fileManagerFolder.resId],
            {search_term: searchValue}
        );
        const formattedFileManagerFolders = fileManagerFolders.map(({id, display_name, root_folder_id}) => {
            return {
                value: {
                    parentFolderId: id,
                    rootFolderName:  root_folder_id[0] !== id ? root_folder_id[1] : ''
                },
                label: display_name
            };
        });
        const selectionGroups = [
            {
                label: _t('Folders'),
                choices: formattedFileManagerFolders,
            }
        ];
        this.state.selectionDisplayGroups = selectionGroups;
        this.state.choices = [
            ...selectionGroups[0].choices,
            ...formattedFileManagerFolders
        ];
    }

    selectFolder(value) {
        this.state.selectedParentFolder = this.state.choices.find(
            (fileManagerFolder) => fileManagerFolder.value.parentFolderId === value.parentFolderId
        );
    }

    async confirmFolderMove() {
        if (!this.state.selectedParentFolder){
            // return if no data selectedParentFolder in the SelectMenu
            return;
        }
        const selectedParentFolder = this.state.selectedParentFolder.value.parentFolderId;
        const params = {};
        if (typeof selectedParentFolder === 'number') {
            params.parent_id = selectedParentFolder;
        } else {
            params.category = selectedParentFolder;
        }
        await this.orm.call(
            'file_manager.file_manager_folder',
            'move_to',
            [this.props.fileManagerFolder.resId],
            params
        );
        // Reload the current folder to apply changes
        await this.props.fileManagerFolder.model.load();
        this.props.close();
    }

    get loggedUserPicture() {
        return `/web/image?model=res.users&field=avatar_128&id=${user.userId}`;
    }

    get moveFolderLabel() {
        return _t('Move "%s" under:', this.props.fileManagerFolder.data.display_name);
    }
}

export default MoveFolderDialog;
