/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { FolderTree } from "./FolderTree";
import { rpc } from "@web/core/network/rpc";

const EXPANDED_PATHS_KEY = "rok_filestore_owl.expandedPaths";

export class FolderTreeContainer extends Component {
    static template = "rok_filestore_owl.FolderTreeContainer";
    static components = { FolderTree };
    static props = { selectedPath: String, onSelect: Function };

    setup() {
        this.onToggle = this.onToggle.bind(this);

        // Load expandedPaths from localStorage
        let expandedPaths = [];
        try {
            expandedPaths = JSON.parse(localStorage.getItem(EXPANDED_PATHS_KEY)) || [];
        } catch {
            expandedPaths = [];
        }

        this.state = useState({
            folders: [],
            expandedPaths,
            loadingPath: "",
        });

        // Load root folders and all expanded branches on initialization
        onWillStart(async () => {
            this.state.folders = await this.fetchFolders("");
            await this.loadExpandedFolders(this.state.folders, this.state.expandedPaths);
        });
    }

    async fetchFolders(path) {
        return await rpc("/rok_filestore_owl/api/folders", { path });
    }

    // Recursively loads children for all paths from expandedPaths
    async loadExpandedFolders(folders, expandedPaths) {
        for (const folder of folders) {
            if (expandedPaths.includes(folder.path)) {
                if (!folder.children) {
                    folder.children = await this.fetchFolders(folder.path);
                }
                if (folder.children && folder.children.length) {
                    await this.loadExpandedFolders(folder.children, expandedPaths);
                }
            }
        }
    }

    async onToggle(path) {
        const idx = this.state.expandedPaths.indexOf(path);
        if (idx >= 0) {
            // Collapse
            this.state.expandedPaths.splice(idx, 1);
        } else {
            // Expand
            this.state.expandedPaths.push(path);
            const folder = this.findFolderByPath(this.state.folders, path);
            if (folder && !folder.children) {
                this.state.loadingPath = path;
                folder.children = await this.fetchFolders(path);
                this.state.loadingPath = "";
            }
        }
        // Save expandedPaths to localStorage
        localStorage.setItem(EXPANDED_PATHS_KEY, JSON.stringify(this.state.expandedPaths));
    }

    findFolderByPath(folders, path) {
        for (const folder of folders) {
            if (folder.path === path) return folder;
            if (folder.children) {
                const found = this.findFolderByPath(folder.children, path);
                if (found) return found;
            }
        }
        return null;
    }
}