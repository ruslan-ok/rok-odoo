/** @odoo-module */

import { Component } from "@odoo/owl";

export class FileGallery extends Component {
  static template = "rok_filestore.FileGallery";
  static props = { files: Array, selectedPath: String, onSelect: Function, onDelete: Function, onUpload: Function };

  get onlyImages() {
    return this.props.files.every(f => f.is_image);
  }
}
