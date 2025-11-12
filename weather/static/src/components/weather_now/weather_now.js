/** @odoo-module **/

import { Component } from "@odoo/owl";

export class WeatherNow extends Component {
    static template = "weather.WeatherNow";
    static props = {
        values: Object,
    };
    setup() {
        this.label_now = ": weather right now";
        this.image = `background-image: ${this.pickUpImage(this.props.values.current.event, this.props.values.sunrise, this.props.values.sunset, this.props.values.current.cloud_cover)}`;
        const dt = new Date(this.props.values.current.event);
        const options = {
            weekday: "short",
            day: "numeric",
            month: "long",
            year: "numeric",
            hour: "numeric",
            minute: "numeric",
        };
        this.dateTime = dt.toLocaleDateString(undefined, options);
        this.href = `/weather/static/src/img/${this.props.values.current.icon_num}.svg`;
        this.windValue = Math.round(+this.props.values.current.wind_speed);
        this.windDirStyle = {transform: `rotate(${this.props.values.current.wind_angle}deg)`};
        this.sign = this.props.values.current.temperature === 0 ? '' : this.props.values.current.temperature > 0 ? '+' : '-';
        this.value = Math.abs(this.props.values.current.temperature);
        this.sunrise = this.props.values.sunrise.split(' ')[1];
        this.sunset = this.props.values.sunset.split(' ')[1];
    }

    pickUpImage(event, sunrise, sunset, cloud_cover) {
        const event_dt = new Date(event);
        const sunrise_dt = new Date(sunrise);
        const sunset_dt = new Date(sunset);
        const event_hr = event_dt.getHours();
        const sunrise_hr = sunrise_dt.getHours();
        const sunset_hr = sunset_dt.getHours();
        const night = (event_hr > sunset_hr || event_hr < sunrise_hr) ? 'n' : 'd';
        let cloud;
        if (cloud_cover <= 25)
            cloud = '0';
        else if (cloud_cover <= 50)
            cloud = '1';
        else if (cloud_cover <= 75)
            cloud = '2';
        else
            cloud = '3';
        const img = `url('/weather/static/src/img/${night}_c${cloud}.jpg')`;
        return img;
    }
}
