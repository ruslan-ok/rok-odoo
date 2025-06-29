import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useService } from "@web/core/utils/hooks";
import { useRecordObserver } from "@web/model/relational_model/utils";

import FileManagerBreadcrumbs from "@file_manager/components/breadcrumbs/breadcrumbs";
import FileManagerIcon from "@file_manager/components/file_manager_icon/file_manager_icon";

import { Component, useState } from "@odoo/owl";

export default class FileManagerHierarchy extends Component {
    static components = {
        Dropdown,
        DropdownItem,
        FileManagerBreadcrumbs,
        FileManagerIcon,
    };
    static props = { record: Object };
    static template = "file_manager.FileManagerHierarchy";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            folderName: this.props.record.data.name,
            isLoadingFolderHierarchy: false,
        });
        useRecordObserver((record) => {
            if (this.state.folderName !== record.data.name) {
                this.state.folderName = record.data.name;
            }
        });
    }

    /**
     * Whether to display the dropdown toggle used to get the folders that are between the root
     * and the parent folder. It is only shown if there are any folders to show (parent_path is
     * of the form "1/2/3/4/", hence length > 4 as condition)
     */
    get displayDropdownToggle() {
        return this.props.record.data.parent_path.split("/").length > 4;
    }

    get isReadonly() {
        return false;
        // return this.props.record.data.is_locked || !this.props.record.data.user_can_write;
    }

    get parentId() {
        return this.props.record.data.parent_id?.[0];
    }

    get parentName() {
        return this.props.record.data.parent_id?.[1];
    }

    get rootId() {
        return this.props.record.data.root_folder_id[0];
    }

    get rootName() {
        return this.props.record.data.root_folder_id[1];
    }

    /**
     * Load the folders that should be shown in the dropdown
     */
    async loadHierarchy() {
        this.folderHierarchy = await this.orm.call(
            "file.manager.folder",
            "get_folder_hierarchy",
            [this.props.record.resId],
            { exclude_folder_ids: [this.rootId, this.parentId, this.props.record.resId] },
        );
        this.state.isLoadingFolderHierarchy = false;
    }

    /**
     * If needed, will show the loading indicator in the dropdown and start the loading
     * of the folders to show in it
     */
    async onBeforeOpen() {
        this.state.isLoadingFolderHierarchy = true;
        this.loadHierarchy();
    }
}
