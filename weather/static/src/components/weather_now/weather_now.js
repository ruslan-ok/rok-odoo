/** @odoo-module **/

import { Component } from "@odoo/owl";

export class WeatherNow extends Component {
    static template = "weather.WeatherNow";
    static props = {
        values: Object,
    };
}
