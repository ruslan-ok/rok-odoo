/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class CryptoToolbar extends Component {
    static template = "crypto.CryptoToolbar";
    static props = {
        toolbar_data: { type: Object, optional: true },
        period_changed: Function
    };
    static defaultProps = {
        toolbar_data: {
            period: "7d",
            current: "",
            change: "",
            amount: "",
            price_url: "",
            amount_url: "",
        },
    };
    static components = { Dropdown, DropdownItem };
    setup() {
        // see https://coinranking.com/api/documentation/coins/coin-details for possible values
        this.periods = [
            { id: "1h", title: "1 Hour" },
            { id: "3h", title: "3 Hours" },
            { id: "12h", title: "12 Hours" },
            { id: "24h", title: "24 Hours" },
            { id: "7d", title: "7 Days" },
            { id: "30d", title: "30 Days" },
            { id: "3m", title: "3 Months" },
            { id: "1y", title: "1 Year" },
            { id: "3y", title: "3 Years" },
            { id: "5y", title: "5 Years" },
        ];
    }

    get toolbarData() {
        return this.props.toolbar_data || this.constructor.defaultProps.toolbar_data;
    }
}
