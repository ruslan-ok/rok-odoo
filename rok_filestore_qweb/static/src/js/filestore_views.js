/** @odoo-module */

import { formView } from '@web/views/form/form_view';
import { registry } from "@web/core/registry";
import { FilestoreFormController } from './filestore_controller.js';
import { FilestoreFormRenderer } from './filestore_renderers.js';

export const filestoreFormView = {
    ...formView,
    Controller: FilestoreFormController,
    Renderer: FilestoreFormRenderer,
    display: {controlPanel: false}
};

registry.category('views').add('filestore_view_form', filestoreFormView);
