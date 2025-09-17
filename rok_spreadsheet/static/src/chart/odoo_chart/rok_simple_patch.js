/** @odoo-module */

// Spreadsheet Enhancements - Chart Patch
// This module patches Chart.js to add smooth lines and thin borders

// Wait for Chart.js to be available
const waitForChart = () => {
    if (typeof Chart !== 'undefined') {
        // Store original Chart constructor
        const OriginalChart = Chart;

        // Patch Chart.js defaults globally
        if (Chart.defaults && Chart.defaults.elements && Chart.defaults.elements.line) {
            // Override global defaults for all line charts
            Chart.defaults.elements.line.tension = 0.4;
            Chart.defaults.elements.line.borderWidth = 1;
        }

        // Patch the Chart constructor
        try {
            // Create a new constructor function
            const EnhancedChart = function(ctx, config) {
                // Enhance line chart configurations
                if (config.type === 'line') {
                    // Enhance global options first
                    if (!config.options) {
                        config.options = {};
                    }
                    if (!config.options.elements) {
                        config.options.elements = {};
                    }
                    if (!config.options.elements.line) {
                        config.options.elements.line = {};
                    }

                    // Force set global defaults for smooth lines
                    config.options.elements.line.tension = 0.4;
                    config.options.elements.line.borderWidth = 1;

                    // Process datasets if they exist
                    if (config.data && config.data.datasets) {
                        config.data.datasets.forEach((dataset) => {
                            // Force apply smooth line settings
                            dataset.lineTension = 0.4;
                            dataset.borderWidth = 1;
                            dataset.cubicInterpolationMode = 'monotone';
                        });
                    }
                }

                const chart = new OriginalChart(ctx, config);

                // Patch the chart after creation to handle async data loading
                if (config.type === 'line') {
                    // Override the update method to patch datasets when data is loaded
                    const originalUpdate = chart.update;
                    chart.update = function(mode) {
                        // Patch datasets after update
                        if (this.data && this.data.datasets) {
                            this.data.datasets.forEach((dataset) => {
                                dataset.lineTension = 0.4;
                                dataset.borderWidth = 1;
                                dataset.cubicInterpolationMode = 'monotone';
                            });
                        }
                        this.config.options.scales.y.beginAtZero = false;

                        return originalUpdate.call(this, mode);
                    };

                    // Also patch the render method
                    const originalRender = chart.render;
                    chart.render = function() {
                        // Final patch before rendering
                        if (this.data && this.data.datasets) {
                            this.data.datasets.forEach((dataset) => {
                                dataset.lineTension = 0.4;
                                dataset.borderWidth = 1;
                                dataset.cubicInterpolationMode = 'monotone';
                            });
                        }

                        return originalRender.call(this);
                    };
                }

                return chart;
            };

            // Copy all properties from original Chart to our enhanced version
            Object.setPrototypeOf(EnhancedChart, OriginalChart);
            Object.assign(EnhancedChart, OriginalChart);

            // Replace Chart in global scope using window object
            if (typeof window !== 'undefined') {
                window.Chart = EnhancedChart;
            }

            // Also try to replace in global scope
            if (typeof global !== 'undefined') {
                global.Chart = EnhancedChart;
            }

        } catch (error) {
            // Fallback: Just modify defaults
            if (Chart.defaults && Chart.defaults.elements && Chart.defaults.elements.line) {
                Chart.defaults.elements.line.tension = 0.4;
                Chart.defaults.elements.line.borderWidth = 1;
            }
        }

    } else {
        setTimeout(waitForChart, 500);
    }
};

// Start waiting for Chart.js
waitForChart();
