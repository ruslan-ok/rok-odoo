/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

export class FormLocation extends Component {
    static template = "weather.FormLocation";

    setup() {
        this.state = useState({
            brsrLoc: this.getBrsrLocOption(),
            location: this.getLocationOption(),
        });
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

    async onChangeBrsrLoc(e) {
        this.state.brsrLoc = e.target.checked;
        await localStorage.setItem('weather-use-browser-location', e.target.checked.toString());
    }

    async save(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const formJson = Object.fromEntries(formData.entries());
        const newLocation = formJson.location.toString();
        this.state.location = newLocation;
        await localStorage.setItem('weather-location', newLocation);
    }
}
