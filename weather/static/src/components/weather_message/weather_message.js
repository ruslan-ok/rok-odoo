/** @odoo-module **/

import { Component } from "@odoo/owl";

export class WeatherMessage extends Component {
    static template = "weather.WeatherMessage";
    static props = {
        message: String,
    };
}
