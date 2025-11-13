/** @odoo-module **/

import { Component } from "@odoo/owl";

export class WeatherForTheWeek extends Component {
    static template = "weather.WeatherForTheWeek";
    static props = {
        values: Object,
    };
    setup() {
        this.label_week = ": weather for the week";
    }
}
