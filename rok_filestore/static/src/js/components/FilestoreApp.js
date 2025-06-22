/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { FolderTreeContainer } from "./FolderTreeContainer";
import { FileGallery } from "./FileGallery";
import { rpc } from "@web/core/network/rpc";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const SELECTED_PATH_KEY = "rok_filestore.selectedPath";

export class FilestoreApp extends Component {
  static template = "rok_filestore.FilestoreApp";
  static components = { FolderTreeContainer, FileGallery };
  static props = {...standardActionServiceProps};

  setup() {
    this.onSelectFolder = this.onSelectFolder.bind(this);

    // Restore selectedPath from localStorage
    let selectedPath = "";
    try {
      selectedPath = localStorage.getItem(SELECTED_PATH_KEY) || "";
    } catch {
      selectedPath = "";
    }

    this.state = useState({
      folders: [],
      selectedPath,
      files: [],
    });

    onWillStart(async () => {
      const folders = await rpc("/rok_filestore/api/folders");
      this.state.folders = folders;

      // Check if selectedPath is still valid
      const isValid = !!folders.find(f => f.path === this.state.selectedPath);
      if (this.state.selectedPath && isValid) {
        await this.onSelectFolder(this.state.selectedPath);
      } else {
        this.state.selectedPath = "";
        localStorage.removeItem(SELECTED_PATH_KEY);
        this.state.files = [];
      }
    });
  }

  async onSelectFolder(path) {
    this.state.selectedPath = path;
    // Save selectedPath to localStorage
    localStorage.setItem(SELECTED_PATH_KEY, path);
    const files = await rpc("/rok_filestore/api/files", { path });
    this.state.files = files.map(f => ({
      ...f,
      url: `/rok_filestore/file?path=${encodeURIComponent(f.path)}`,
      thumbUrl: f.is_image
        ? `/rok_filestore/thumbnail?path=${encodeURIComponent(f.path)}&size=128`
        : null,
    }));
  }

  async onSelectFile(path) {
    console.log(path);
  }
}
