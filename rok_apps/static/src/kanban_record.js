/** @odoo-module **/

import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { RokAppsWidget } from "./rok_apps_widget";
import { RokAppsKanbanCompiler } from "./kanban_compiler";

KanbanRecord.components = {
    ...KanbanRecord.components,
    RokAppsWidget,
};

KanbanRecord.Compiler = RokAppsKanbanCompiler;
