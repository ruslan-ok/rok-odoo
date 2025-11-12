/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";

export class FormLocation extends Component {
    static template = "weather.FormLocation";
    static props = {
        location: String,
        useBrowserLocation: Boolean,
    };

    setup() {
        this.locationInput = useRef("locationInput");
    }

    getBrsrLocOption() {
        const ubl = localStorage.getItem('weather-use-browser-location');
        if (ubl === undefined)
            return true;
        return (ubl === 'true');
    }

    getLocationOption() {
        const lctn = localStorage.getItem('weather-location');
        if (lctn === undefined)
            return '';
        return lctn;
    }

    async toggleBrowserLocation() {
        this.props.useBrowserLocation = !this.props.useBrowserLocation;
        await localStorage.setItem('weather-use-browser-location', this.props.useBrowserLocation.toString());
    }

    async save() {
        const newLocation = this.locationInput.el.value;
        this.props.location = newLocation;
        await localStorage.setItem('weather-location', newLocation);
    }
}
