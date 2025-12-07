/** @odoo-module **/

import { registry } from "@web/core/registry";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { graphView } from "@web/views/graph/graph_view";
import { Crypto } from "../../components/crypto";
import { CryptoModel } from "../../components/crypto_model";
import { ReportViewPeriods } from "../../components/report_view_periods";
import { useState, useEffect, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

const viewRegistry = registry.category("views");

export class CryptoGraphRenderer extends GraphRenderer {
    static template = "crypto.CryptoGraphRenderer";
    static components = { ...GraphRenderer.components, Crypto, ReportViewPeriods };
    setup() {
        super.setup();
        this.state = useState({data: {}});
        this.model.metaData.periods = [
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
            { id: "10y", title: "10 Years" },
        ];
        const period = this.getPeriodOption();
        this.model.metaData.period = period;
        this.model.metaData.error = "";
        this.title = "Crypto";
        this.onPeriodSelected = this.onPeriodSelected.bind(this);

        onWillStart(async () => {
            await this.getData(period);
        });

        useEffect(
            () => { this.getData(this.model.metaData.period); },
            () => [this.model.metaData.period],
        );
    }

    async getData(period) {
        try {
            const response = await rpc("/crypto/data", {
                period: period,
            });
            if (response.result != "ok") {
                this.model.updateMetaData({ error: response.info });
            } else {
                this.model.updateMetaData({ error: "" });
                this.state.data = response.data;
            }
        } catch (error) {
            this.model.updateMetaData({ error: error.message || error });
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
        this.model.updateMetaData({ period });
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
