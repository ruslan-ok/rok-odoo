/** @odoo-module **/

import { RokAppsWidget } from "@rok_apps/rok_apps_widget";
import { registerRokAppsWidget } from "@rok_apps/rok_apps_widget_registry";
import { useState, useEffect } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { Anthropometry } from "./components/anthropometry";
import { AnthropometryToolbar } from "./components/anthropometry_toolbar";

export class HealthRokAppsWidget extends RokAppsWidget {
    static template = "health.RokAppsWidget";
    static props = ["record"];
    static components = { ...RokAppsWidget.components, Anthropometry, AnthropometryToolbar };
    setup() {
        this.state = useState({
            error: "",
            data: {datasets: []},
            toolbar_data: {
                period: this.getPeriodOption(),
                current: "",
                trend: "",
            },
        });

        this.onPeriodSelected = this.onPeriodSelected.bind(this);
        this.onValueAdded = this.onValueAdded.bind(this);
        useEffect(
            () => { this.getData(); },
            () => [this.state.toolbar_data.period],
        );
    }
    async getData() {
        try {
            const response = await rpc("/anthropometry/data", {
                period: this.state.toolbar_data.period,
            });
            if (response.result != "ok") {
                this.state.error = response.info;
            } else {
                this.state.error = "";
                this.state.data = response.data.chart_data;
                this.state.toolbar_data.current = response.data.current.toFixed(2);
                this.state.toolbar_data.trend = response.data.trend.toFixed(2);
            }
        } catch (error) {
            this.state.error = error.message || error;
        }
    }

    getPeriodOption() {
        const period = localStorage.getItem("anthropo-period");
        if (period === undefined || period === null)
            return "1w";
        return period;
    }

    async onPeriodSelected(period) {
        localStorage.setItem("anthropo-period", period);
        this.state.toolbar_data.period = period;
        await this.getData();
    }

    async onValueAdded(value) {
        try {
            const response = await rpc("/anthropometry/add", {value: value});
            if (response.result != "ok") {
                this.state.error = response.info;
            } else {
                this.state.error = "";
                await this.getData();
            }
        } catch (error) {
            this.state.error = error.message || error;
        }
    }
}

// Register the widget for the "Health" app
registerRokAppsWidget("Health", HealthRokAppsWidget);
