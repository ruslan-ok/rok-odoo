/** @odoo-module **/

import { registry } from "@web/core/registry";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { graphView } from "@web/views/graph/graph_view";
import { Crypto } from "../../components/crypto";
import { CryptoModel } from "../../components/crypto_model";
import { CryptoToolbar } from "../../components/crypto_toolbar";
import { useState, useEffect } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

const viewRegistry = registry.category("views");

export class CryptoGraphRenderer extends GraphRenderer {
    static template = "crypto.CryptoGraphRenderer";
    static components = { ...GraphRenderer.components, Crypto, CryptoToolbar };
    setup() {
        super.setup();
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
        this.title = "Crypto";
        this.onPeriodSelected = this.onPeriodSelected.bind(this);

        useEffect(
            () => { this.getData(this.state.toolbar_data.period); },
            () => [this.state.toolbar_data.period],
        );
    }

    async getData(period) {
        try {
            const response = await rpc("/crypto/data", {
                period: period,
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
        await this.getData(period);
    }
};

export const CryptoGraphView = {
    ...graphView,
    Model: CryptoModel,
    Renderer: CryptoGraphRenderer,
    buttonTemplate: "crypto.CryptoGraphView.Buttons",
};

viewRegistry.add("crypto_graph", CryptoGraphView);
