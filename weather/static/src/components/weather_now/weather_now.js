/** @odoo-module **/

import { Component, onWillUpdateProps } from "@odoo/owl";

export class WeatherNow extends Component {
    static template = "weather.WeatherNow";
    static props = {
        values: Object,
    };
    setup() {
        this.label_now = ": weather right now";
        this.image = "";
        this.dateTime = "";
        this.href = "";
        this.windValue = 0;
        this.windDirStyle = {};
        this.sign = "";
        this.value = 0;
        this.sunrise = "";
        this.sunset = "";
        onWillUpdateProps((nextProps) => this.onWillUpdateProps(nextProps));
        this.onWillUpdateProps(this.props);
    }

    onWillUpdateProps(nextProps) {
        // Guard against undefined values
        if (!nextProps.values || !nextProps.values.current) {
            return;
        }
        this.image = `background-image: ${this.pickUpImage(nextProps.values.current.event, nextProps.values.sunrise, nextProps.values.sunset, nextProps.values.current.cloud_cover)}`;
        const dt = new Date(nextProps.values.current.event);
        const options = {
            weekday: "short",
            day: "numeric",
            month: "long",
            year: "numeric",
            hour: "numeric",
            minute: "numeric",
        };
        this.dateTime = dt.toLocaleDateString(undefined, options);
        this.href = `/weather/static/src/img/${nextProps.values.current.icon_num}.svg`;
        this.windValue = Math.round(+nextProps.values.current.wind_speed);
        this.windDirStyle = {transform: `rotate(${nextProps.values.current.wind_angle}deg)`};
        this.sign = nextProps.values.current.temperature === 0 ? '' : nextProps.values.current.temperature > 0 ? '+' : '-';
        this.value = Math.abs(nextProps.values.current.temperature);
        if (nextProps.values.sunrise) {
            this.sunrise = nextProps.values.sunrise.split(' ')[1];
        }
        if (nextProps.values.sunset) {
            this.sunset = nextProps.values.sunset.split(' ')[1];
        }
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
