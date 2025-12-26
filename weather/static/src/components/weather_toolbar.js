/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";

export class WeatherToolbar extends Component {
    static template = "weather.WeatherToolbar";
    static props = {
        toolbar_data: { type: Object, optional: true },
        onLocationSelected: Function,
        onSetLocality: Function,
        onPeriodSelected: Function,
    };
    static defaultProps = {
        toolbar_data: {
            location: "browser",
            locality: "",
            period: "now",
        },
    };
    setup() {
        this.localityInput = useRef("localityInput");
        this.onSetLocality = this.onSetLocality.bind(this);
    }

    get toolbarData() {
        return this.props.toolbar_data || this.constructor.defaultProps.toolbar_data;
    }

    onSetLocality() {
        const locality = this.localityInput.el.value;
        this.props.onSetLocality(locality);
    }
}
