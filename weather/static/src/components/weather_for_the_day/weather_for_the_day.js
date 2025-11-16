/** @odoo-module **/

import { Component, onWillUpdateProps } from "@odoo/owl";
import { getDayName, getDayDate, getDayColor, getIconHref, getHourNum, getTempBarsInfo, checkNight, getWindColor } from '../weather_utils';

export class WeatherForTheDay extends Component {
    static template = "weather.WeatherForTheDay";
    static props = {
        values: Object,
    };
    setup() {
        this.label_day = ": weather for the day";
        this.days = [];
        this.hours = [];
        this.icons = [];
        this.titlesTemp = [];
        this.tempBars = [];
        this.titlesWind = [];
        this.winds = [];
        this.titlesPreci = [];
        this.precipitation = [];
        onWillUpdateProps((nextProps) => this.onWillUpdateProps(nextProps));
        this.onWillUpdateProps(this.props);
    }

    onWillUpdateProps(nextProps) {
        let d1_day;
        let d2_day;
        let d1_day_str;
        let d2_day_str;
        let d1_span = 0;
        let d1_span_correct = 0;
        let d2_span_correct = 0;
        for (let i = 0; i < nextProps.values.for_day.length; i++) {
            const dt = new Date(nextProps.values.for_day[i].event);
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
        for (let i = 0; i < nextProps.values.for_day.length; i++) {
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

        const sunrise_dt = new Date(nextProps.values.sunrise);
        const sunset_dt = new Date(nextProps.values.sunset);
        const sunrise = sunrise_dt.getHours();
        const sunset = sunset_dt.getHours();

        this.days = nextProps.values.for_day.map((hour, index) => {
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

        this.hours = nextProps.values.for_day.map((hour, index) => {
            let cellClass = ['hour-name'];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            const hourNum = getHourNum(hour.event, d1_span_correct);
            let name = '';
            if (index % 3 === 0) {
                name = hourNum.toString();
            }
            return {key: hour.event, class: cellClass.join(' '), name: name};
        });

        this.icons = nextProps.values.for_day.map((hour, index) => {
            let cellClass = [];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            let href = '';
            const ndx = index - d1_span_correct;
            if (ndx >= 0 && index % 3 === 1) {
                const icon_num = nextProps.values.for_day[ndx].icon_num;
                href = getIconHref(icon_num);
            }
            cellClass.push('icon-td');
            return {key: hour.event, class: cellClass.join(' '), href: href};
        });

        this.titlesTemp = nextProps.values.for_day.map((hour, index) => {
            let cellClass = [];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            let name = '';
            if (index === 0) {
                cellClass.push('overflow-td');
                name = 'Temperature, °C';
            }
            return {key: hour.event, class: cellClass.join(' '), name: name};
        });

        const tempBarHeights = getTempBarsInfo(nextProps.values.for_day, false);
        this.tempBars = nextProps.values.for_day.map((hour, index) => {
            let cellClass = ['bar day-column'];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            let topStyle = '';
            let midStyle = '';
            let botStyle = '';
            let avgTemp = '';
            if (index < tempBarHeights.length) {
                topStyle = `height: ${tempBarHeights[index].top}px`;
                midStyle = `height: 15px; background-color: ${tempBarHeights[index].color}; border-top: 1px solid ${tempBarHeights[index].borderTop}; border-bottom: 1px solid ${tempBarHeights[index].borderBot}`;
                botStyle = `height: 25px`;
                avgTemp = index % 3 === 1 ? tempBarHeights[index].avgTemp : '';
            }
            return {
                key: hour.event,
                class: cellClass.join(' '),
                topStyle: topStyle,
                midStyle: midStyle,
                botStyle: botStyle,
                avgTemp: avgTemp,
            };
        });

        this.titlesWind = nextProps.values.for_day.map((hour, index) => {
            let cellClass = [];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            let name = '';
            if (index === 0) {
                cellClass.push('overflow-td');
                name = 'Wind, m/s';
            }
            return {key: hour.event, class: cellClass.join(' '), name: name};
        });

        this.winds = nextProps.values.for_day.map((hour) => {
            let cellClass = ['day-column hour-wind'];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            const value = Math.round(+hour.wind_speed);
            const directionStyle = `transform: rotate(${hour.wind_angle}deg);`;
            const valueStyle = `color: ${getWindColor(value)}`;
            return {
                key: hour.event,
                class: cellClass.join(' '),
                value: value,
                directionStyle: directionStyle,
                valueStyle: valueStyle,
            };
        });

        this.titlesPreci = nextProps.values.for_day.map((hour, index) => {
            let cellClass = [];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            let name = '';
            if (index === 0) {
                cellClass.push('overflow-td');
                name = 'Precipitation, mm';
            }
            return {key: hour.event, class: cellClass.join(' '), name: name};
        });

        const maxPreci = tempBarHeights.map(x => x.precipitation).reduce(function(prev, curr) { return prev > curr ? prev : curr; });
        this.precipitation = nextProps.values.for_day.map((hour) => {
            let cellClass = ['day-column hour-perci-td'];
            checkNight(cellClass, hour.event, d1_span_correct, sunrise, sunset);
            const maxHeight = 20;
            const value = +hour.prec_total;
            const color = value === 0 ? 'gray' : '#62b2ed';
            const height = maxPreci === 0 ? 0 : maxHeight * value / maxPreci;
            const valueStyle = `color: ${color}`;
            const heightStyle = `height: ${height}px`;
            return {
                key: hour.event,
                class: cellClass.join(' '),
                value: value,
                valueStyle: valueStyle,
                heightStyle: heightStyle,
            };
        });
    }
}
