/** @odoo-module */

import { Component } from "@odoo/owl";

export class FolderTree extends Component {
  static template = "rok_filestore.FolderTree";
  static props = { folders: Array, selectedPath: String, onSelect: Function };
  static components = { FolderTree };
}
