/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class AnthropometryToolbar extends Component {
    static template = "rok_health.AnthropometryToolbar";
    static props = {
        toolbar_data: { type: Object, optional: true },
        period_changed: Function,
        value_added: Function,
    };
    static defaultProps = {
        toolbar_data: {
            period: "1w",
            current: "",
            trend: "",
        },
    };
    static components = { Dropdown, DropdownItem };
    setup() {
        this.periods = [
            { id: "1w", title: "1 Week" },
            { id: "1m", title: "1 Month" },
            { id: "3m", title: "3 Months" },
            { id: "1y", title: "1 Year" },
            { id: "3y", title: "3 Years" },
            { id: "10y", title: "10 Years" },
        ];
        this.valueInput = useRef("valueInput");
        this.onAddValue = this.onAddValue.bind(this);
    }

    get toolbarData() {
        return this.props.toolbar_data || this.constructor.defaultProps.toolbar_data;
    }

    onAddValue() {
        const value = parseFloat(this.valueInput.el.value);
        if (value) {
            this.props.value_added(value);
            this.valueInput.el.value = "";
        }
    }
}
