/** @odoo-module **/

import { Component } from "@odoo/owl";

export class WeatherForTheDay extends Component {
    static template = "weather.WeatherForTheDay";
    static props = {
        values: Object,
    };
}
