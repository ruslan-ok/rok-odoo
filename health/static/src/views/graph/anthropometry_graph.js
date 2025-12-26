/** @odoo-module **/

import { registry } from "@web/core/registry";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { graphView } from "@web/views/graph/graph_view";
import { Anthropometry } from "../../components/anthropometry";
import { AnthropometryToolbar } from "../../components/anthropometry_toolbar";
import { useState, useEffect, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

const viewRegistry = registry.category("views");

export class AnthropometryGraphRenderer extends GraphRenderer {
    static template = "health.AnthropometryGraphRenderer";
    static components = { ...GraphRenderer.components, Anthropometry, AnthropometryToolbar };
    setup() {
        super.setup();
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

        onWillStart(async () => {
            await this.getData(this.state.toolbar_data.period);
        });

        useEffect(
            () => { this.getData(this.state.toolbar_data.period); },
            () => [this.state.toolbar_data.period],
        );
    }

    async getData(period) {
        try {
            const response = await rpc("/anthropometry/data", {period: period});
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
        await this.getData(period);
    }

    async onAddValue(value) {
        try {
            const response = await rpc("/anthropometry/add", {value: value});
            if (response.result != "ok") {
                this.state.error = response.info;
            } else {
                await this.getData(this.state.toolbar_data.period);
            }
        } catch (error) {
            this.state.error = error.message || error;
        }
    }
};

export const AnthropometryGraphView = {
    ...graphView,
    Renderer: AnthropometryGraphRenderer,
    buttonTemplate: "health.AnthropometryGraphView.Buttons",
};

viewRegistry.add("anthropometry_graph", AnthropometryGraphView);
