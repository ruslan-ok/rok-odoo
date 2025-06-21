/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { FolderTree } from "./FolderTree";
import { rpc } from "@web/core/network/rpc";

export class FolderTreeContainer extends Component {
    static template = "rok_filestore.FolderTreeContainer";
    static components = { FolderTree };

    setup() {
        this.state = useState({
            folders: [],
            expandedPaths: [],
            loadingPath: "",
            selectedPath: "",
        });

        // Загрузка корневых папок при инициализации
        onWillStart(async () => {
            this.state.folders = await this.fetchFolders("");
        });
    }

    async fetchFolders(path) {
        // Замените на ваш реальный RPC вызов
        return await rpc("/rok_filestore/api/folders", { path });
    }

    async onToggle(path) {
        const idx = this.state.expandedPaths.indexOf(path);
        if (idx >= 0) {
            // Сворачиваем
            this.state.expandedPaths.splice(idx, 1);
        } else {
            // Раскрываем
            this.state.expandedPaths.push(path);
            // Найти папку по пути и загрузить детей, если ещё не загружены
            const folder = this.findFolderByPath(this.state.folders, path);
            if (folder && !folder.children) {
                this.state.loadingPath = path;
                folder.children = await this.fetchFolders(path);
                this.state.loadingPath = "";
            }
        }
    }

    onSelect(path) {
        this.state.selectedPath = path;
        // Можно добавить дополнительную логику при выборе папки
    }

    // Рекурсивный поиск папки по пути
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