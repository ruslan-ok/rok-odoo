/** @odoo-module */

import { formView } from '@web/views/form/form_view';
import { registry } from "@web/core/registry";
import { FileManagerFormController } from './file_manager_controller.js';
import { FileManagerFormRenderer } from './file_manager_renderers.js';

export const fileManagerFormView = {
    ...formView,
    Controller: FileManagerFormController,
    Renderer: FileManagerFormRenderer,
    display: {controlPanel: false}
};

registry.category('views').add('file_manager_view_form', fileManagerFormView);
