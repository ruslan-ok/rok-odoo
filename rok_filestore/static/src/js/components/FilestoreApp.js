/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { FolderTree } from "./FolderTree";
import { FileGallery } from "./FileGallery";
import { rpc } from "@web/core/network/rpc";

export class FilestoreApp extends Component {
  static template = "rok_filestore.FilestoreApp";
  static components = { FolderTree, FileGallery };


  setup() {
    this.onSelectFolder = this.onSelectFolder.bind(this);
    this.state = useState({
      folders: [],
      selectedPath: "",
      files: [],
    });

    onWillStart(async () => {
      const folders = await rpc("/rok_filestore/api/folders");
      this.state.folders = folders;
    });
  }

  async onSelectFolder(path) {
    this.state.selectedPath = path;
    const files = await rpc("/rok_filestore/api/files", { path });
    this.state.files = files.map(f => ({
      ...f,
      url: `/rok_filestore/file?path=${f.path}`,
    }));
  }

  async onSelectFile(path) {
    console.log(path);
  }
}
