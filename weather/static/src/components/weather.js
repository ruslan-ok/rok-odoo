/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { FormLocation } from "./form_location/form_location";
import { WeatherMessage } from "./weather_message/weather_message";
import { WeatherNow } from "./weather_now/weather_now";
import { WeatherForTheDay } from "./weather_for_the_day/weather_for_the_day";
import { WeatherForTheWeek } from "./weather_for_the_week/weather_for_the_week";

export class Weather extends Component {
    static template = "weather.Weather";
    static components = {
        FormLocation,
        WeatherMessage,
        WeatherNow,
        WeatherForTheDay,
        WeatherForTheWeek,
    };
    setup() {
        this.state = useState({
            data: null,
            loading: true,
            error: null,
            period: 'now',
            location: this.getLocationOption(),
            useBrowserLocation: this.getBrowserLocationOption(),
        });
        this.label_now = "Сейчас";
        this.label_day = "Сутки";
        this.label_week = "Неделя";
        this.cr_url = "https://www.meteosource.com";
        this.cr_info = "Powered by Meteosource";
        this.ms_href = "/weather/static/src/img/7.svg";

        onWillStart(async () => {
            async function getCoord() {
                const pos = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject);
                });

                return {
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude,
                };
            }
            try {
                let lat = "";
                let lon = "";
                if (this.state.useBrowserLocation) {
                    const coord = await getCoord();
                    lat = coord.lat;
                    lon = coord.lon;
                }
                const response = await rpc("/weather/data", {
                    location: this.state.location,
                    lat: lat,
                    lon: lon,
                });
                if (response.result != "ok") {
                    this.state.error = response.info;
                    this.state.period = "";
                    throw new Error(this.state.error);
                }
                this.state.data = response.data;
                this.state.period = "now";
            } catch (error) {
                this.state.error = error.message || error;
            } finally {
                this.state.loading = false;
            }
        });
    }

    getLocationOption() {
        const location = localStorage.getItem('weather-location');
        if (location === undefined)
            return "";
        return location;
    }

    getBrowserLocationOption() {
        const ubl = localStorage.getItem('weather-use-browser-location');
        if (ubl === undefined)
            return true;
        return (ubl === 'true');
    }

    setPeriodOption(period) {
        this.state.period = period;
    }
}

registry.category("actions").add("weather.action", Weather);
