/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
// import { ArticleSelectionDialog } from "../../components/article_selection_dialog/article_selection_dialog";
// import { ArticleTemplatePickerDialog } from "@knowledge/components/article_template_picker_dialog/article_template_picker_dialog";
import { browser } from '@web/core/browser/browser'
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import {
    FilestoreSidebarFavoriteSection,
    FilestoreSidebarPrivateSection,
    FilestoreSidebarSharedSection,
    FilestoreSidebarWorkspaceSection
} from "./sidebar_section";
import { localization } from "@web/core/l10n/localization";
import { user } from "@web/core/user";
import { throttleForAnimation } from "@web/core/utils/timing";
import { useNestedSortable } from "@web/core/utils/nested_sortable";
import { useService } from "@web/core/utils/hooks";
import { useRecordObserver } from "@web/model/relational_model/utils";

import { Component, onWillStart, reactive, useRef, useState, useChildSubEnv } from "@odoo/owl";

export const SORTABLE_TOLERANCE = 10;

/**
 * Main Sidebar component. Its role is mainly to fetch and manage the folders
 * to show and allow to reorder them. It updates the info of the current
 * folder each time the props are updated.
 * The folders are stored in the state and have the following shape:
 * - {string} category,
 * - {array} child_ids,
 * - {string} icon,
 * - {boolean} is_folder_item,
 * - {boolean} is_locked,
 * - {boolean} is_user_favorite,
 * - {string} name,
 * - {number} parent_id,
 * - {boolean} user_can_write,
 * - {boolean} has_children,
 */
export class FilestoreSidebar extends Component {
    static props = {
        record: Object,
    };
    static template = "rok_filestore_qweb.Sidebar";
    static components = {
        FilestoreSidebarFavoriteSection,
        FilestoreSidebarPrivateSection,
        FilestoreSidebarSharedSection,
        FilestoreSidebarWorkspaceSection,
    };
    
    setup() {
        super.setup();

        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.orm = useService("orm");

        this.favoriteTree = useRef("favoriteTree");
        this.mainTree = useRef("mainTree");

        this.currentData = {};

        this.storageKeys = {
            size: "rok_filestore_qweb.sidebarSize",
            unfoldedFolders: "rok_filestore_qweb.unfolded.ids",
            unfoldedFavorites: "rok_filestore_qweb.unfolded.favorite.ids",
        };

        // Get set of unfolded ids and sync it with the local storage (any
        // change will trigger a write in the local storage)
        this.unfoldedFoldersIds = reactive(
            new Set(localStorage.getItem(this.storageKeys.unfoldedFolders)?.split(";").map(Number)),
            () => localStorage.setItem(this.storageKeys.unfoldedFolders, Array.from(this.unfoldedFoldersIds).join(";"))
        );
        this.unfoldedFavoritesIds = reactive(
            new Set(localStorage.getItem(this.storageKeys.unfoldedFavorites)?.split(";").map(Number)),
            () => localStorage.setItem(this.storageKeys.unfoldedFavorites, Array.from(this.unfoldedFavoritesIds).join(";"))
        );

        useChildSubEnv({
            fold: this.fold.bind(this),
            getFolder: this.getFolder.bind(this),
            model: this.props.record.model,
            unfold: this.unfold.bind(this),
        });

        this.state = useState({
            dragging: false,
            sidebarSize: localStorage.getItem(this.storageKeys.size) || 300,
        });

        this.loadFolders();

        // Resequencing of the favorite folders
        useNestedSortable({
            ref: this.favoriteTree,
            edgeScrolling: {
                speed: 10,
                threshold: 15,
            },
            preventDrag: (el) => {
                // Prevent the reordering of child folders that are readonly within the favorite
                // section.
                return (
                    !el.parentElement.classList.contains("o_tree") &&
                    el.classList.contains("readonly")
                );
            },
            tolerance: SORTABLE_TOLERANCE,
            onDrop: ({ element, next, parent }) => {
                if (!parent) {
                    // Favorite resequence
                    // const folderId = parseInt(element.dataset.folderId);
                    // const beforeId = next ? parseInt(next.dataset.folderId) : false;
                    // this.resequenceFavorites(folderId, beforeId);
                } else {
                    // Child of favorite resequence
                    const folder = this.getFolder(parseInt(element.dataset.folderId));
                    const parentId = parseInt(parent.dataset.folderId);
                    const currentPosition = {
                        category: folder.category,
                        parentId: folder.parent_id,
                        beforeFolderId:
                            parseInt(element.nextElementSibling?.dataset.folderId) || false,
                    };
                    const newPosition = {
                        category: folder.category,
                        parentId: parentId,
                        beforeFolderId: parseInt(next?.dataset.folderId) || false,
                    };
                    this.moveFolder(folder, currentPosition, newPosition);
                }
            },
        });

        // Resequencing and rehierarchisation of folders
        useNestedSortable({
            ref: this.mainTree,
            groups: () => this.isInternalUser ? ".o_section" : ".o_section[data-section='private']",
            connectGroups: () => this.isInternalUser,
            nest: true,
            preventDrag: (el) => el.classList.contains("readonly"),
            tolerance: SORTABLE_TOLERANCE,
            onDragStart: () => this.state.dragging = true,
            onDragEnd: () => this.state.dragging = false,
            /**
             * @param {DOMElement} element - dropped element
             * @param {DOMElement} next - element before which the element was dropped
             * @param {DOMElement} group - initial (=current) group of the dropped element
             * @param {DOMElement} newGroup - group in which the element was dropped
             * @param {DOMElement} parent - parent element of where the element was dropped
             * @param {DOMElement} placeholder - hint element showing the current position
             */
            onDrop: async ({element, next, group, newGroup, parent, placeholder}) => {
                const folder = this.getFolder(parseInt(element.dataset.folderId));
                // Dropped on trash, move the folder to the trash
                if (newGroup.classList.contains("o_knowledge_sidebar_trash")) {
                    this.moveToTrash(folder);
                    return;
                }
                const parentId = parent ? parseInt(parent.dataset.folderId) : false;
                // Dropped on restricted position (child of readonly or shared root)
                if (placeholder.classList.contains('bg-danger')) {
                    this.rejectDrop(folder, parentId);
                    return;
                }
                const currentPosition = {
                    category: folder.category,
                    parentId: folder.parent_id,
                    beforeFolderId: parseInt(element.nextElementSibling?.dataset.folderId) || false,
                };
                const newPosition = {
                    category: newGroup.dataset.section,
                    parentId: parentId,
                    beforeFolderId: parseInt(next?.dataset.folderId) || false,
                };
                this.moveFolder(folder, currentPosition, newPosition);
            },
            /**
             * @param {DOMElement} element - moved element
             * @param {DOMElement} parent - parent element of where the element was moved
             * @param {DOMElement} group - initial (=current) group of the moved element
             * @param {DOMElement} newGroup - group in which the element was moved
             * @param {DOMElement} prevPos.parent - element's parent before the move
             * @param {DOMElement} placeholder - hint element showing the current position
             */
            onMove: ({element, parent, group, newGroup, prevPos, placeholder}) => {
                if (prevPos.parent) {
                    const prevParent = this.getFolder(parseInt(prevPos.parent.dataset.folderId));
                    // Remove caret if folder has no child
                    if (!prevParent.has_children ||
                        prevParent.child_ids.length === 1 &&
                        prevParent.child_ids[0] === parseInt(element.dataset.folderId)
                    ) {
                        prevPos.parent.classList.remove('o_folder_has_children');
                    }
                }
                if (parent) {
                    // Cannot add child to readonly folders, unless it is the
                    // current parent.
                    const currentParentId = element.parentElement.parentElement.dataset.folderId;
                    const targetParentId = parent.dataset.folderId;
                    if (currentParentId !== targetParentId && parent.classList.contains('readonly')) {
                        placeholder.classList.add('bg-danger');
                        return;
                    }
                    // Add caret
                    parent.classList.add('o_folder_has_children');
                } else if (newGroup.dataset.section === "shared") {
                    // Private folders cannot be dropped in the shared section
                    const folder = this.getFolder(parseInt(element.dataset.folderId));
                    if (folder.category === "private") {
                        placeholder.classList.add('bg-danger');
                        return;
                    }
                }
                placeholder.classList.remove('bg-danger');
            },
        });

        onWillStart(async () => {
            this.isInternalUser = await user.hasGroup('base.group_user');
        });

        useRecordObserver(async (record) => {
            const nextDataParentId = record.data.parent_id ? record.data.parent_id[0] : false;
            // During the first load, `loadFolders` is still pending and the component is in its
            // loading state. However, because of OWL reactive implementation (uses a Proxy),
            // record data still has to be read in order to subscribe to later changes, even if
            // nothing is done with that data on the first call. This subscription is what allows
            // this callback to be called i.e. when the name of the folder is changed, reflecting
            // the change in the sidebar. See useRecordObserver, effect, reactive implementations
            // for further details.
            const folder = this.getFolder(record.resId) || {
                id: record.resId,
                name: record.data.name,
                icon: record.data.icon,
                category: record.data.category,
                parent_id: nextDataParentId,
                is_locked: record.data.is_locked,
                // user_can_write: record.data.user_can_write,
                // is_folder_item: record.data.is_folder_item,
                is_user_favorite: record.data.is_user_favorite,
                child_ids: [],
            };
            if (this.state.folders[record.resId]) {
                // if (record.data.is_folder_item !== folder.is_folder_item) {
                //     if (record.data.is_folder_item) {
                //         // Folder became item, remove it from the sidebar
                //         this.removeFolder(folder);
                //     } else {
                //         // Item became folder, add it in the sidebar
                //         this.insertFolder(folder, {
                //             parentId: folder.parent_id
                //         });
                //         this.showFolder(folder);
                //     }
                // }
                if (record.data.is_user_favorite !== folder.is_user_favorite) {
                    if (record.data.is_user_favorite) {
                        // Add the folder to the favorites tree
                        this.state.favoriteIds.push(folder.id);
                    } else {
                        // Remove the folder from the favorites tree
                        this.state.favoriteIds.splice(this.state.favoriteIds.indexOf(folder.id), 1);
                    }
                }
                if ((nextDataParentId !== folder.parent_id || record.data.category !== folder.category) &&
                    (record.data.parent_id !== this.currentData.parent_id || record.data.category !== this.currentData.category)) {
                    // Folder changed position ("Moved to")
                    if (!this.getFolder(nextDataParentId)) {
                        // Parent is not loaded, reload the tree to show moved
                        // folder in the sidebar
                        await this.loadFolders();
                        this.showFolder(this.getFolder(record.resId));
                    } else {
                        this.repositionFolder(folder, {
                            parentId: nextDataParentId,
                            category: record.data.category,
                        });
                    }
                }
                // Update values used to display the current folder in the sidebar
                Object.assign(folder, {
                    name: record.data.name,
                    icon: record.data.icon,
                    is_locked: record.data.is_locked,
                    // user_can_write: record.data.user_can_write,
                    // is_folder_item: record.data.is_folder_item,
                    is_user_favorite: record.data.is_user_favorite,
                });
            } else if (!this.state.loading) {  // New folder, add it in the state and sidebar
                if (record.data.is_user_favorite) {
                    // Favoriting an folder that is not shown in the main
                    // tree (hidden child, item, or child of restricted)
                    this.state.favoriteIds.push(record.resId);
                }
                this.state.folders[folder.id] = folder;
                // Don't add new items in the sidebar
                // if (!record.data.is_folder_item) {
                //     await this.insertFolder(folder, {
                //         category: folder.category,
                //         parentId: folder.parent_id,
                //     });
                //     // Make sure the folder is visible
                //     this.showFolder(folder);
                //     if (nextDataParentId && this.getFolder(nextDataParentId)?.is_user_favorite) {
                //         this.unfold(nextDataParentId, true);
                //     }
                // }
                await this.insertFolder(folder, {
                    category: folder.category,
                    parentId: folder.parent_id,
                });
                // Make sure the folder is visible
                this.showFolder(folder);
                if (nextDataParentId && this.getFolder(nextDataParentId)?.is_user_favorite) {
                    this.unfold(nextDataParentId, true);
                }
            }

            this.currentData = {
                parent_id: record.data.parent_id,
                category: record.data.category,
            };
        });
        this.env.bus.addEventListener("rok_filestore_qweb.sidebar.insertNewFolder", async ({ detail }) => {
            if (this.getFolder(detail.folderId)) {
                // Folder already in the sidebar
                return;
            }
            const parent = detail.parentId ? this.getFolder(detail.parentId) : false;
            const newFolder = {
                id: detail.folderId,
                name: detail.name,
                icon: detail.icon,
                parent_id: parent ? parent.id : false,
                category: parent ? parent.category : false,
                is_locked: false,
                // user_can_write: true,
                // is_folder_item: false,
                is_user_favorite: false,
                child_ids: [],
            };
            this.state.folders[newFolder.id] = newFolder;
            await this.insertFolder(newFolder, {
                parentId: newFolder.parent_id,
                category: parent ? parent.category : false
            });
        });
    }

    /**
     * Open the templates dialog
     */
    browseTemplates() {
        // this.dialog.add(FolderTemplatePickerDialog, {
        //     onLoadTemplate: async folderTemplateId => {
        //         await this.actionService.doAction("knowledge.ir_actions_server_knowledge_home_page", {
        //             stackPosition: "replaceCurrentAction",
        //             additionalContext: {
        //                 res_id: await this.orm.call("knowledge.folder", "create_folder_from_template", [
        //                     folderTemplateId
        //                 ])
        //             }
        //         });
        //     }
        // });
    }

    /**
     * Change the category of an folder, and of all its descendants.
     * @param {Object} folder
     * @param {String} category
     */
    async changeCategory(folder, category) {
        folder.category = category;
        if (folder.id === this.props.record.id) {
            // Reload current record to propagate changes
            if (await this.props.record.isDirty()) {
                await this.props.record.save();
            } else {
                await this.props.record.model.load();
            }
        }
        for (const childId of folder.child_ids) {
            this.changeCategory(this.getFolder(childId), category);
        }
    }

    /**
     * Create a new folder (and open it).
     * @param {String} - category
     * @param {integer} - targetParentId
     */
    createFolder(category, targetParentId) {
        try {
            this.env.createFolder(category, targetParentId);
        } catch {
            // Could not create folder, reload tree in case some permission changed
            this.loadFolders();
        }
    }

    /**
     * Fold an folder.
     * @param {integer} folderId: id of folder
     * @param {boolean} isFavorite: whether to fold in favorite tree
     */
    fold(folderId, isFavorite) {
        if (isFavorite) {
            this.unfoldedFavoritesIds.delete(folderId);
        } else {
            this.unfoldedFoldersIds.delete(folderId);
        }
    }

    /**
     * Get the folder stored in the state given its id.
     * @param {integer} folderId - Id of the folder 
     * @returns {Object} folder
     */
    getFolder(folderId) {
        return this.state.folders[folderId];
    }

    /**
     * Get the array of folder ids stored in the state from the given category
     * (eg. this.state.workspaceIds for workspace).
     * @param {String} category
     * @returns {Array} array of folders ids
     */
    getCategoryIds(category) {
        return this.state[`${category}Ids`];
    }

    /**
     * Insert the given folder at the given position in the sidebar.
     * @param {Object} folder - folder stored in the state
     * @param {Object} position
     * @param {integer} position.beforeFolderId
     * @param {String} position.category
     * @param {integer} position.parentId
     *  
     */
    async insertFolder(folder, position) {
        if (position.parentId) {
            const parent = this.getFolder(position.parentId);
            if (parent) {
                // Make sure the existing children are loaded if parent has any
                if (!this.unfoldedFoldersIds.has(parent.id)) {
                    await this.unfold(parent.id, false);
                    if (parent.child_ids.includes(folder.id)) {
                        return;
                    }
                }
                // Position it at the right position w.r. to the other children
                // if the parent is not yet aware of the child folder (eg when
                // moving, the folder is moved in frontend, then if the user
                // confirms, the folder is moved in backend)
                if (position.beforeFolderId) {
                    parent.child_ids.splice(parent.child_ids.indexOf(position.beforeFolderId), 0, folder.id);
                } else {
                    parent.child_ids.push(folder.id);
                }
                parent.has_children = true;
            }
        } else {
            // Add folder in the list of folders of the new category, at the right position
            const categoryIds = this.getCategoryIds(position.category);
            if (categoryIds) {
                if (position.beforeFolderId) {
                    categoryIds.splice(categoryIds.indexOf(position.beforeFolderId), 0, folder.id);
                } else {
                    categoryIds.push(folder.id);
                }
            }
        }
    }

    /**
     * Check if the given folder is an ancestor of the active one.
     * @param {integer} folderId
     * @returns {Boolean}
     */
    isAncestor(folderId) {
        let folder = this.getFolder(this.props.record.resId);
        while (folder) {
            if (folder.id === folderId) {
                return true;
            }
            folder = this.getFolder(folder.parent_id);
        }
        return false;
    }

    /**
     * Load the folders to show in the sidebar and store them in the state.
     * One loops through the folders fetched to create a mapping id:folder
     * that allows easy access of the folders, add the folders in their correct categories
     * and add their children. One uses the parent_id field to fill the 
     * child_ids arrays because a simple read of the child_ids field would
     * return items (which should not be included in the sidebar), and the
     * folders would not be sorted correctly.
     */
    async loadFolders() {
        this.state.loading = true;
        // Remove already loaded folders
        Object.assign(this.state, {
            folders: {},
            favoriteIds: [],
            workspaceIds: [],
            sharedIds: [],
            privateIds: [],
        });
        const res = await this.orm.call(
            this.props.record.resModel,
            "get_sidebar_folders",
            [this.props.record.resId],
            { unfolded_ids: [...this.unfoldedFoldersIds, ...this.unfoldedFavoritesIds] }
        );
        const children = {};
        for (const folder of res.folders) {
            this.state.folders[folder.id] = {
                ...folder,
                child_ids: children[folder.id] ? children[folder.id] : [],
            };
            // Items could be shown in the favorite tree as root folders, but
            // they should not be shown as children of other folders
            // if (!folder.is_folder_item) {
            if (folder.parent_id) {
                const parent = this.getFolder(folder.parent_id);
                if (parent) {
                    parent.child_ids.push(folder.id);
                } else {
                    // Store children temporarily to add them to the parent
                    // when the parent will be added to the state in this loop.
                    if (children[folder.parent_id]) {
                        children[folder.parent_id].push(folder.id);
                    } else {
                        children[folder.parent_id] = [folder.id];
                    }
                }
            } else {
                this.getCategoryIds(folder.category).push(folder.id);
            }
            // }
        }
        const ancestorRootFolderId = res.active_folder_accessible_root_id;
        if (ancestorRootFolderId) {
            this.getCategoryIds(this.getFolder(ancestorRootFolderId).category).push(
                ancestorRootFolderId
            );
        }
        this.state.favoriteIds = res.favorite_ids;
        this.showFolder(this.getFolder(this.props.record.resId));
        this.state.loading = false;
        this.resetUnfoldedFolders();
    }

    /**
     * Load the children of a given folder
     * @param {object} folder
     */
    async loadChildren(folder) {
        const children = await this.orm.searchRead(
            this.props.record.resModel,
            // [['parent_id', '=', folder.id], ['is_folder_item', '=', false]],
            // ['name', 'icon', 'is_locked', 'user_can_write', 'has_children'],
            [['parent_id', '=', folder.id]],
            ['name', 'icon', 'is_locked', 'has_children'],
            {
                'load': 'None',
                'order': 'id',
            }
        );
        for (const child of children) {
            folder.child_ids.push(child.id);
            if (this.getFolder(child.id)) {
                // Folder was already loaded (if it is in the favorites)
                continue;
            }
            this.state.folders[child.id] = {
                ...child,
                parent_id: folder.id,
                child_ids: [],
                category: folder.category,
                // is_folder_item: false,
                is_user_favorite: false,
            };
        }
    }

    /**
     * Try to move the given folder to the given position (change its parent/
     * category) and update its position in the sidebar.
     * If the move will change the permissions of the folder, show a
     * confirmation dialog.
     * @param {Object} folder
     * @param {Object} currentPosition
     * @param {integer} position.beforeFolderId 
     * @param {String} position.category
     * @param {integer} position.parentId
     * @param {Object} newPosition
     * @param {integer} newPosition.beforeFolderId 
     * @param {String} newPosition.category
     * @param {integer} newPosition.parentId
     */
    async moveFolder(folder, currentPosition, newPosition) {
        const confirmMove = async (folder, position) => {
            if (this.props.record.resId === folder.id && await this.props.record.isDirty()) {
                await this.props.record.save();
            }
            try {
                await this.orm.call(
                    this.props.record.resModel,
                    'move_to',
                    [folder.id],
                    {
                        category: position.category,
                        parent_id: position.parentId,
                        before_folder_id: position.beforeFolderId,
                    }
                );
            } catch (error) {
                // Reload the folder tree to show potential modifications
                // done by another user that could cause the failure.
                this.loadFolders();
                throw error;
            }
            // Reload the current folder as the move will impact its data
            await this.props.record.model.load();
        };

        // Move the folder in the sidebar
        this.repositionFolder(folder, newPosition);
        // Permissions won't change, no need to ask for confirmation
        if (currentPosition.category === newPosition.category) {
            confirmMove(folder, newPosition);
        } else {
            // Show confirmation dialog, and move folder back to its original
            // position if the user cancels the move 
            const emoji = folder.icon || '';
            const name = folder.name;
            let message;
            let confirmLabel;
            if (newPosition.category === 'workspace') {
                message = _t(
                    'Are you sure you want to move "%(icon)s%(title)s" to the Workspace? It will be shared with all internal users.',
                    { icon: emoji, title: name || _t("Untitled") }
                );
                confirmLabel = _t("Move to Workspace");
            } else if (newPosition.category === 'private') {
                message = _t(
                    'Are you sure you want to move "%(icon)s%(title)s" to private? Only you will be able to access it.',
                    { icon: emoji, title: name || _t("Untitled") }
                );
                confirmLabel = _t("Move to Private");
            } else if (newPosition.category === 'shared') {
                if (newPosition.parentId) {
                    const parent = this.getFolder(newPosition.parentId);
                    message = _t(
                        'Are you sure you want to move "%(icon)s%(title)s" under "%(parentIcon)s%(parentTitle)s"? It will be shared with the same persons.',
                        {
                            icon: emoji,
                            title: name || _t("Untitled"),
                            parentIcon: parent.icon || "",
                            parentTitle: parent.name || _t("Untitled"),
                        }
                    );
                } else {
                    message = _t(
                        'Are you sure you want to move "%(icon)s%(title)s" to the Shared section? It will be shared with all listed members.',
                        { icon: emoji, title: name || _t("Untitled") }
                    );
                }
                confirmLabel = _t('Move to Shared')
            }
            this.dialog.add(ConfirmationDialog, {
                body: message,
                confirmLabel: confirmLabel,
                confirm: () => confirmMove(folder, newPosition),
                cancel: () => {
                    // Move folder back to its position
                    this.repositionFolder(folder, currentPosition);
                },
            });
        } 
    }

    /**
     * Move an folder to the trash, and remove it from the sidebar.
     * @param {Object} folder
     */
    async moveToTrash(folder) {
        try {
            await this.orm.call(
                "rok.filestore.folder",
                "action_send_to_trash",
                [folder.id],
            );
        } catch {
            await this.loadFolders();
            return;
        }
        // If the folder moved to the trash is an ancestor of the active
        // folder, redirect to first accessible folder.
        if (this.isAncestor(folder.id)) {
            this.actionService.doAction(
                await this.orm.call('rok.filestore.folder', 'action_home_page', [false]),
                {stackPosition: 'replaceCurrentAction'}
            );
        } else {
            this.removeFolder(folder);
            this.removeFavorite(folder);
        }
    }

    /**
     * Open the command palette if the user is an internal user, and open the
     * folder selection dialog if the user is a portal user
     */
    onSearchBarClick() {
        if (this.isInternalUser) {
            this.env.services.command.openMainPalette({searchValue: '?'});
        // } else {
        //     this.dialog.add(
        //         FolderSelectionDialog,
        //         {
        //             title: _t('Search a Folder...'),
        //             confirmLabel: _t('Open'),
        //             folderSelected: (folder) => this.env.openFolder(folder.folderId),
        //         }
        //     );
        }
    }

    /**
     * Show a dialog explaining why the given folder cannot be moved to the
     * target position.
     * @param {folder}
     * @param {parentId}
     */
    rejectDrop(folder, parentId) {
        let message;
        if (parentId) {
            const parent = this.getFolder(parentId);
            message = _t(
                'Could not move "%(icon)s%(title)s" under "%(parentIcon)s%(parentTitle)s", because you do not have write permission on the latter.',
                {
                    icon: folder.icon || "",
                    title: folder.name,
                    parentIcon: parent.icon || "",
                    parentTitle: parent.name,
                }
            );
        } else {
            message = _t('You need at least 2 members for the Folder to be shared.');
        }
        this.dialog.add(ConfirmationDialog, {
            confirmLabel: _t("Close"),
            title: _t("Move cancelled"),
            body: message,
        });
    }

    /**
     * Remove the given folder from the sidebar.
     * @param {Object} folder
     */
    removeFolder(folder) {
        if (folder.parent_id) {
            // Remove folder from array of children of its parent
            const parent = this.getFolder(folder.parent_id);
            if (parent) {
                const folderIdx = parent.child_ids.indexOf(folder.id);
                if (folderIdx !== -1) {
                    parent.child_ids.splice(parent.child_ids.indexOf(folder.id), 1);
                    // Removed last child of the parent folder
                    if (!parent.child_ids.length) {
                        this.fold(parent.id);
                        this.fold(parent.id, true);
                        parent.has_children = false;
                    }
                }
            }
        } else {
            // Remove folder from list of folders category
            const categoryIds = this.getCategoryIds(folder.category);
            const folderIdx = categoryIds.indexOf(folder.id);
            if (folderIdx !== -1) {
                categoryIds.splice(folderIdx, 1);
            }
        }
    }

    /**
     * Remove the given folder from the list of favorites.
     * @param {Object} folder
     */
    removeFavorite(folder) {
        const favoriteIdx = this.state.favoriteIds.indexOf(folder.id);
        if (favoriteIdx !== -1) {
            this.state.favoriteIds.splice(favoriteIdx, 1);
        }
     }

    /**
     * Change the position of an folder in the sidebar.
     * @param {Object} folder
     * @param {Object} position
     * @param {integer} position.beforeFolderId 
     * @param {String} position.category
     * @param {integer} position.parentId
     */
    async repositionFolder(folder, position) {
        this.removeFolder(folder);
        await this.insertFolder(folder, position);
        // Change the parent of the folder
        if (folder.parent_id !== position.parentId) {
            folder.parent_id = position.parentId;
        }
        // Change category of folder and every descendant
        if (folder.category !== position.category) {
            this.changeCategory(folder, position.category);
        }
        // Make sure the folder is visible
        this.showFolder(folder);
    }

    /**
     * Updates the sequence of favorite folders for the current user.
     * @param {integer} folderId - Id of the moved favorite folder
     * @param {integer} beforeId - Id of the favorite folder after
     *      which the folder is moved
     */
    // resequenceFavorites(folderId, beforeId) {
    //     this.state.favoriteIds.splice(this.state.favoriteIds.indexOf(folderId), 1);
    //     if (beforeId) {
    //         this.state.favoriteIds.splice(this.state.favoriteIds.indexOf(beforeId), 0, folderId);
    //     } else {
    //         this.state.favoriteIds.push(folderId);
    //     }
    //     this.orm.call("rok_filestore_qweb.folder.favorite", "resequence_favorites", [false], {
    //         folder_ids: this.state.favoriteIds,
    //     });
    // }

    /**
     * User could have unfolded ids in its local storage of folders that are
     * not shown in its sidebar anymore (trashed, converted to items, hidden,
     * permission change). This method will reset the list of ids in the local
     * storage using only the folders that are shown to the user, so that we
     * do not load the folders using a list containing a lot of useless ids. 
     */
    resetUnfoldedFolders() {
        this.unfoldedFoldersIds.forEach(id => {
            if (!this.getFolder(id)) {
                this.unfoldedFoldersIds.delete(id);
            }
        });
        this.unfoldedFavoritesIds.forEach(id => {
            if (!this.getFolder(id)) {
                this.unfoldedFavoritesIds.delete(id);
            }
        });
    }

    /**
     * Resize the sidebar horizontally.
     */
    resize() {
        const isRtl = localization.direction === "rtl";
        const onPointerMove = throttleForAnimation(event => {
            event.preventDefault();
            this.state.sidebarSize = isRtl ? document.documentElement.clientWidth - event.pageX : event.pageX;
            browser.dispatchEvent(new Event("resize"));
        });
        const onPointerUp = () => {
            document.removeEventListener('pointermove', onPointerMove);
            document.body.style.cursor = "auto";
            document.body.style.userSelect = "auto";
            localStorage.setItem(this.storageKeys.size, this.state.sidebarSize);
            browser.dispatchEvent(new Event("resize"));
        };
        // Add style to root element because resizing has a transition delay,
        // meaning that the cursor is not always on top of the resizer.
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
        document.addEventListener('pointermove', onPointerMove);
        document.addEventListener('pointerup', onPointerUp, {once: true});
    }

    /**
     * Make sure the given folder is shown in the sidebar by unfolding every
     * folder until a root folder is met.
     * @param {object} folder - folder to show in the sidebar
     */
    showFolder(folder) {
        while (folder && folder.parent_id && folder.parent_id in this.state.folders) {
            // Unfold in the main tree, without loading the children
            this.unfold(folder.parent_id, false);
            folder = this.getFolder(folder.parent_id);
        }
    }

    /** Unfold an folder.
     * @param {integer} folderId: id of folder
     * @param {boolean} isFavorite: whether to unfold in favorite tree
     */        
    async unfold(folderId, isFavorite) {
        const folder = this.getFolder(folderId);
        // Load the children of the folder if it has not been unfolded yet
        if (folder.has_children && !folder.child_ids.length) {
            await this.loadChildren(folder);
        }
        if (isFavorite) {
            this.unfoldedFavoritesIds.add(folderId);
        } else {
            this.unfoldedFoldersIds.add(folderId);
        }
    }
}
