/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useRef, onWillStart, useEffect, onWillUnmount } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { Chart } from "chart.js";

export class Crypto extends Component {
    static template = "crypto.Crypto";
    static props = { period: String, error: String, title: String, data: Object };
    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
        });

        useEffect(() => this.renderChart());
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
            const config = this.getChartConfig();
            this.chart = new Chart(this.canvasRef.el, config);
        }
    }

    getLineChartData() {
        const { cumulated } = this.model.metaData;
        const data = this.model.data;
        for (let index = 0; index < data.datasets.length; ++index) {
            const dataset = data.datasets[index];
            const itemColor = getColor(index, colorScheme, data.datasets.length);
            dataset.backgroundColor = getCustomColor(
                colorScheme,
                lightenColor(itemColor, 0.5),
                darkenColor(itemColor, 0.5)
            );
            dataset.cubicInterpolationMode = "monotone";
            dataset.borderColor = itemColor;
            dataset.borderWidth = 2;
            dataset.hoverBackgroundColor = dataset.borderColor;
            dataset.pointRadius = 3;
            dataset.pointHoverRadius = 6;
            if (cumulated) {
                let accumulator = dataset.cumulatedStart;
                dataset.data = dataset.data.map((value) => {
                    accumulator += value;
                    return accumulator;
                });
            }
            if (data.labels.length === 1) {
                // shift of the real value to right. This is done to
                // center the points in the chart. See data.labels below in
                // Chart parameters
                dataset.data.unshift(undefined);
                dataset.trueLabels.unshift(undefined);
                dataset.domains.unshift(undefined);
            }
            dataset.pointBackgroundColor = dataset.borderColor;
        }
        // center the points in the chart (without that code they are put
        // on the left and the graph seems empty)
        data.labels = data.labels.length > 1 ? data.labels : ["", ...data.labels, ""];
        return data;
    }

    prepareOptions() {
        const options = {
            maintainAspectRatio: false,
            scales: this.getScaleOptions(),
            plugins: {
                legend: this.getLegendOptions(),
                tooltip: this.getTooltipOptions(),
            },
            elements: this.getElementOptions(),
            onResize: () => {
                this.resizeChart(options);
            },
            animation: this.getAnimationOptions(),
        };
        options.interaction = {
            mode: "index",
            intersect: false,
        };
        return options;
    }

    getChartConfig() {
        let data = this.getLineChartData();
        const options = this.prepareOptions();
        const config = { data, options, type: "line" };
        config.plugins = [gridOnTop];
        return config;
    }
}
