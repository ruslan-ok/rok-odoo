/** @odoo-module **/

import { registry } from "@web/core/registry";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { graphView } from "@web/views/graph/graph_view";
import { Weather } from "../../components/weather";
import { useState, useEffect, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { WeatherToolbar } from "../../components/weather_toolbar";

const viewRegistry = registry.category("views");

export class WeatherGraphRenderer extends GraphRenderer {
    static template = "weather.WeatherGraphRenderer";
    static components = { ...GraphRenderer.components, Weather, WeatherToolbar };
    setup() {
        super.setup();
        this.state = useState(
            {
                data: {},
                error: "",
                toolbar_data: {
                    location: this.getLocationOption(),
                    locality: this.getLocalityOption(),
                    period: this.getPeriodOption(),
                }});
        this.onPeriodSelected = this.onPeriodSelected.bind(this);
        this.onLocationSelected = this.onLocationSelected.bind(this);
        this.onSetLocality = this.onSetLocality.bind(this);
        this.title = "Weather";

        onWillStart(async () => {
            await this.getData();
        });

        useEffect(
            () => { this.getData(); },
            () => [this.state.toolbar_data.location, this.state.toolbar_data.locality],
        );
    }

    async getCoord() {
        const pos = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject);
        });

        return {
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
        };
    }

    async getData() {
        try {
            let lat = "";
            let lon = "";
            let locality = this.state.toolbar_data.locality;
            if (this.state.toolbar_data.location === 'browser' || locality === '') {
                const coord = await this.getCoord();
                lat = coord.lat;
                lon = coord.lon;
                locality = "";
            }
            const response = await rpc("/weather/data", {
                location: locality,
                lat: lat,
                lon: lon,
            });
            if (response.result != "ok") {
                this.state.error = response.info;
                this.state.toolbar_data.period = "error";
            } else {
                this.state.error = "";
                this.state.data = response.data;
            }
        } catch (error) {
            this.state.error = error.message || error;
            this.state.toolbar_data.period = "error";
        }
        this.getTitle(this.state.toolbar_data.period);
    }

    getTitle(period) {
        if (!this.state.toolbar_data.locality) {
            this.title = "Weather";
        } else {
            let title = "weather ";
            switch (period) {
                case "now":
                    title += "right now";
                    break;
                case "day":
                    title += "for the day";
                    break;
                case "week":
                    title += "for the week";
                    break;
            }
            const locality = this.state.data.place;
            this.title = `${locality}: ${title}`;
        }
    }

    getLocationOption() {
        const location = localStorage.getItem('weather-location');
        if (location === undefined || location === null)
            return "browser";
        return location;
    }
    getLocalityOption() {
        const locality = localStorage.getItem('weather-locality');
        if (locality === undefined || locality === null)
            return "";
        return locality;
    }
    getPeriodOption() {
        const period = localStorage.getItem('weather-period');
        if (period === undefined || period === null)
            return "now";
        return period;
    }
    onPeriodSelected(period) {
        localStorage.setItem('weather-period', period);
        this.state.toolbar_data.period = period;
        this.getTitle(period);
    }
    onLocationSelected(location) {
        localStorage.setItem('weather-location', location);
        this.state.toolbar_data.location = location;
    }
    onSetLocality(locality) {
        localStorage.setItem('weather-locality', locality);
        this.state.toolbar_data.locality = locality;
    }
};

export const WeatherGraphView = {
    ...graphView,
    Renderer: WeatherGraphRenderer,
    buttonTemplate: "weather.WeatherGraphView.Buttons",
};

viewRegistry.add("weather_graph", WeatherGraphView);
