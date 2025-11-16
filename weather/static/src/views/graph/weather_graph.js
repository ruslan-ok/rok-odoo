/** @odoo-module **/

import { registry } from "@web/core/registry";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { graphView } from "@web/views/graph/graph_view";
import { Weather } from "../../components/weather";
import { useRef, useState, useEffect, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

const viewRegistry = registry.category("views");

export class WeatherGraphRenderer extends GraphRenderer {
    static template = "weather.WeatherGraphRenderer";
    static components = { ...GraphRenderer.components, Weather };
    setup() {
        super.setup();
        this.state = useState({data: {}});
        this.model.metaData.location = this.getLocationOption();
        this.model.metaData.locality = this.getLocalityOption();
        this.model.metaData.period = this.getPeriodOption();
        this.model.metaData.error = "";
        this.onPeriodSelected = this.onPeriodSelected.bind(this);
        this.onLocationSelected = this.onLocationSelected.bind(this);
        this.onSetLocality = this.onSetLocality.bind(this);
        this.localityInput = useRef("localityInput");
        this.title = "Weather";

        onWillStart(async () => {
            await this.getData();
        });

        useEffect(
            () => { this.getData(); },
            () => [this.model.metaData.location, this.model.metaData.locality],
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
            let locality = this.model.metaData.locality;
            if (this.model.metaData.location === 'browser' || locality === '') {
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
                this.model.updateMetaData({ period: "error", error: response.info });
            } else {
                this.model.updateMetaData({ error: "" });
                this.state.data = response.data;
            }
        } catch (error) {
            this.model.updateMetaData({ period: "error", error: error.message || error });
        }
        this.getTitle(this.model.metaData.period);
    }

    getTitle(period) {
        if (!this.model.metaData.locality) {
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
        this.model.updateMetaData({ period });
        this.getTitle(period);
    }
    onLocationSelected(location) {
        localStorage.setItem('weather-location', location);
        this.model.updateMetaData({ location });
    }
    onSetLocality() {
        const locality = this.localityInput.el.value;
        this.model.updateMetaData({ locality });
        localStorage.setItem('weather-locality', locality);
    }
};

export const WeatherGraphView = {
    ...graphView,
    Renderer: WeatherGraphRenderer,
    buttonTemplate: "weather.WeatherGraphView.Buttons",
};

viewRegistry.add("weather_graph", WeatherGraphView);
