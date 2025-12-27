/** @odoo-module **/

import { loadJS } from "@web/core/assets";
import { Component } from "@odoo/owl";
import { useRef, onWillStart, useEffect, onWillUnmount } from "@odoo/owl";

export class Anthropometry extends Component {
    static template = "rok_health.Anthropometry";
    static props = { chart_data: Object, error: String };
    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onWillStart(async () => {
            await loadJS("/rok_apps/static/lib/chart.js");
            await loadJS("/rok_apps/static/lib/chartjs-adapter-date-fns.bundle.min.js");
        });

        useEffect(() => this.renderChart(), () => [this.props.chart_data]);
        onWillUnmount(this.onWillUnmount);
    }

    onWillUnmount() {
        if (this.chart) {
            this.chart.destroy();
        }
    }

    renderChart() {
        if (this.chart) {
            this.chart.destroy();
        }
        if (this.canvasRef.el) {
            const ctx = this.canvasRef.el;
            this.chart = new Chart(ctx, this.props.chart_data);
        }
    }
}
