/** @odoo-module **/

import { Component } from "@odoo/owl";
import { getDayName, getDayDate, getDayColor, getIconHref, getHourNum, getTempBarsInfo, checkNight, getWindColor } from '../weather_utils';

export class WeatherForTheDay extends Component {
    static template = "weather.WeatherForTheDay";
    static props = {
        values: Object,
    };
    setup() {
        this.label_day = ": weather for the day";

        let d1_day;
        let d2_day;
        let d1_day_str;
        let d2_day_str;
        let d1_span = 0;
        let d1_span_correct = 0;
        let d2_span_correct = 0;
        for (let i = 0; i < this.props.values.for_day.length; i++) {
            const dt = new Date(this.props.values.for_day[i].event);
            if (i === 0) {
                d1_day = dt.getDate();
                d1_day_str = dt.toString();
            }
            else {
                if (d2_day === undefined && d1_day !== dt.getDate()) {
                    d2_day = dt.getDate();
                    d2_day_str = dt.toString();
                }
            }
            if (d2_day === undefined)
                d1_span++;
        }

        if (d1_span % 3 === 1) {
            d1_span_correct--;
            d2_span_correct++;
        }

        if (d1_span % 3 === 2) {
            d1_span_correct++;
            d2_span_correct--;
        }

        let aggs = [];
        let curr = [];
        for (let i = 0; i < this.props.values.for_day.length; i++) {
            curr.push(i);
            if (curr.length === 3 || (aggs.length === 0 && curr.length === 2 && d1_span_correct === 1)) {
                aggs.push(curr);
                curr = [];
            }
            if (i === 0 && d2_span_correct === 1)
                curr = [];
        }
        if (curr.length > 1)
            aggs.push(curr);

        const sunrise_dt = new Date(this.props.values.sunrise);
        const sunset_dt = new Date(this.props.values.sunset);
        const sunrise = sunrise_dt.getHours();
        const sunset = sunset_dt.getHours();

        this.days = this.props.values.for_day.map((hour, index) => {
            let cellClass = [];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);

            let name = '';
            if (index === 0) {
                name = getDayName(d1_day_str) + ' ' + getDayDate(hour.event, 0);
                cellClass.push('day-name overflow-td ' + getDayColor(hour.event));
            }
            else {
                if (d2_day !== undefined && index === (d1_span + d1_span_correct)) {
                    name = getDayName(d2_day_str) + ' ' + getDayDate(hour.event, 0);
                    cellClass.push('day-name overflow-td ' + getDayColor(hour.event));
                }
            }
            return {key: hour.event, class: cellClass.join(' '), name: name};
        });

        this.hours = this.props.values.for_day.map((hour, index) => {
            let cellClass = ['hour-name'];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            const hourNum = getHourNum(hour.event, d1_span_correct);
            let name = '';
            if (index % 3 === 0) {
                name = hourNum.toString();
            }
            return {key: hour.event, class: cellClass.join(' '), name: name};
        });

        this.icons = this.props.values.for_day.map((hour, index) => {
            let cellClass = [];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            let href = '';
            const ndx = index - d1_span_correct;
            if (ndx >= 0 && index % 3 === 1) {
                const icon_num = this.props.values.for_day[ndx].icon_num;
                href = getIconHref(icon_num);
            }
            cellClass.push('icon-td');
            return {key: hour.event, class: cellClass.join(' '), href: href};
        });
    }
}
