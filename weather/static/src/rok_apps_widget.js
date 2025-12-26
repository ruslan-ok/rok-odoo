/** @odoo-module **/

import { RokAppsWidget } from "@rok_apps/rok_apps_widget";
import { registerRokAppsWidget } from "@rok_apps/rok_apps_widget_registry";
import { Weather } from "@weather/components/weather";
import { useState, useEffect } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { WeatherToolbar } from "./components/weather_toolbar";

export class WeatherRokAppsWidget extends RokAppsWidget {
    static template = "weather.RokAppsWidget";
    static props = ["record"];
    static components = { ...RokAppsWidget.components, Weather, WeatherToolbar };
    setup() {
        this.state = useState({
            error: "",
            data: {},
            toolbar_data: {
                location: this.getLocationOption(),
                locality: this.getLocalityOption(),
                period: this.getPeriodOption(),
            },
        });
        this.title = "";

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
        this.title = `${this.state.data.place}: ${title}`;
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
}

// Register the widget for the "Weather" app
registerRokAppsWidget("Weather", WeatherRokAppsWidget);
