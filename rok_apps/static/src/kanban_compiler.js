/** @odoo-module **/

import { KanbanCompiler } from "@web/views/kanban/kanban_compiler";
import { createElement } from "@web/core/utils/xml";

export class RokAppsKanbanCompiler extends KanbanCompiler {
    setup() {
        super.setup();
        this.compilers.push({
            selector: "RokAppsWidget",
            fn: this.compileRokAppsWidget,
        });
    }

    compileRokAppsWidget(el, params) {
        const recordExpr = "__comp__.props.record";
        const compiled = createElement("RokAppsWidget");
        compiled.setAttribute("record", recordExpr);
        for (const { name, value } of el.attributes) {
            if (name !== "record" && name !== "t-att-record") {
                compiled.setAttribute(name, value);
            }
        }
        for (const child of el.childNodes) {
            const compiledChild = this.compileNode(child, params);
            if (compiledChild) {
                compiled.appendChild(compiledChild);
            }
        }
        return compiled;
    }
}
