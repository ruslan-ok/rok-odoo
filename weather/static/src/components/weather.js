/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
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
            values: {},
        });
        this.label_now = "Сейчас";
        this.label_day = "Сутки";
        this.label_week = "Неделя";
        this.cr_url = "https://www.meteosource.com";
        this.cr_info = "Powered by Meteosource";
        this.ms_href = "/static/widgets/weather/7.svg";
        onWillStart(async () => {
            try {
                const response = await fetch("/weather/data", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {},
                        id: Date.now(),
                    }),
                    credentials: "same-origin",
                });
                if (!response.ok) {
                    this.state.error = `HTTP ${response.status}`;
                    throw new Error(this.state.error);
                }
                const payload = await response.json();
                const response_data = payload.result;
                if (response_data.result === "error") {
                    this.state.error = response_data.info;
                    throw new Error(this.state.error);
                }
                this.state.data = response_data.data;
            } catch (error) {
                this.state.error = error.message || error;
            } finally {
                this.state.loading = false;
            }
        });
    }

    setPeriodOption(period) {
        this.state.period = period;
    }
}

registry.category("actions").add("weather.action", Weather);
