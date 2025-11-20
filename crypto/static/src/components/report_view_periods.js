/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class ReportViewPeriods extends Component {
    static template = "crypto.ReportViewPeriods";
    static components = {
        Dropdown,
        DropdownItem,
    };
    static props = {
        periods: { type: Object },
        period: { type: String },
        onPeriodSelected: { type: Function },
    };
}
