/** @odoo-module **/

import { Component } from "@odoo/owl";
import { WeatherMessage } from "./weather_message/weather_message";
import { WeatherNow } from "./weather_now/weather_now";
import { WeatherForTheDay } from "./weather_for_the_day/weather_for_the_day";
import { WeatherForTheWeek } from "./weather_for_the_week/weather_for_the_week";

export class Weather extends Component {
    static template = "weather.Weather";
    static props = { period: String, error: String, title: String, data: Object };
    static components = {
        WeatherMessage,
        WeatherNow,
        WeatherForTheDay,
        WeatherForTheWeek,
    };
    setup() {
        this.cr_url = "https://www.meteosource.com";
        this.cr_info = "Powered by Meteosource";
        this.ms_href = "/weather/static/src/img/7.svg";
    }
}
