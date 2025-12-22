/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { RokAppsWidget } from "./rok_apps_widget";

KanbanRenderer.components = {
    ...KanbanRenderer.components,
    RokAppsWidget,
};
