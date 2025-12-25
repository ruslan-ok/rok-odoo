/** @odoo-module **/

import { RokAppsWidget } from "@rok_apps/rok_apps_widget";
import { registerRokAppsWidget } from "@rok_apps/rok_apps_widget_registry";
import { useState, onWillStart, useEffect } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { Crypto } from "./components/crypto";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class CryptoRokAppsWidget extends RokAppsWidget {
    static template = "crypto.RokAppsWidget";
    static props = ["record"];
    static components = { ...RokAppsWidget.components, Crypto, Dropdown, DropdownItem };
    setup() {
        // see https://coinranking.com/api/documentation/coins/coin-details
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
        ],
        this.state = useState({
            period: this.getPeriodOption(),
            error: "",
            data: {datasets: []},
        });
        this.onPeriodSelected = this.onPeriodSelected.bind(this);

        onWillStart(async () => {
            await this.getData();
        });

        useEffect(
            () => { this.getData(); },
            () => [this.state.period],
        );
    }
    async getData() {
        try {
            const response = await rpc("/crypto/data", {
                period: this.state.period,
            });
            if (response.result != "ok") {
                this.state.error = response.info;
            } else {
                this.state.error = "";
                this.state.data = response.data.chart_data;
            }
        } catch (error) {
            this.state.error = error.message || error;
        }
    }

    getPeriodOption() {
        const period = localStorage.getItem("crypto-period");
        if (period === undefined || period === null)
            return "7d";
        return period;
    }

    async onPeriodSelected(period) {
        localStorage.setItem("crypto-period", period);
        this.state.period = period;
        await this.getData();
    }
}

// Register the widget for the "Crypto" app
registerRokAppsWidget("Crypto", CryptoRokAppsWidget);
