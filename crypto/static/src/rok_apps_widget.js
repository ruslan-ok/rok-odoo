/** @odoo-module **/

import { RokAppsWidget } from "@rok_apps/rok_apps_widget";
import { registerRokAppsWidget } from "@rok_apps/rok_apps_widget_registry";
import { useState, useEffect } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { Crypto } from "./components/crypto";
import { CryptoToolbar } from "./components/crypto_toolbar";

export class CryptoRokAppsWidget extends RokAppsWidget {
    static template = "crypto.RokAppsWidget";
    static props = ["record"];
    static components = { ...RokAppsWidget.components, Crypto, CryptoToolbar };
    setup() {
        this.state = useState({
            error: "",
            data: {datasets: []},
            toolbar_data: {
                period: this.getPeriodOption(),
                current: "",
                change: "",
                amount: "",
                price_url: "",
                amount_url: "",
            },
        });

        this.onPeriodSelected = this.onPeriodSelected.bind(this);

        useEffect(
            () => { this.getData(); },
            () => [this.state.toolbar_data.period],
        );
    }
    async getData() {
        try {
            const response = await rpc("/crypto/data", {
                period: this.state.toolbar_data.period,
            });
            if (response.result != "ok") {
                this.state.error = response.info;
            } else {
                this.state.error = "";
                this.state.data = response.data.chart_data;
                this.state.toolbar_data.current = Math.round(response.data.current).toLocaleString();
                this.state.toolbar_data.change = response.data.change.toFixed(2);
                this.state.toolbar_data.amount = Math.round(response.data.amount).toLocaleString();
                this.state.toolbar_data.price_url = response.data.price_url || "";
                this.state.toolbar_data.amount_url = response.data.amount_url || "";
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
        this.state.toolbar_data.period = period;
        await this.getData();
    }
}

// Register the widget for the "Crypto" app
registerRokAppsWidget("Crypto", CryptoRokAppsWidget);
