/** @odoo-module **/

import { Component, onWillUpdateProps } from "@odoo/owl";
import { getTempBarsInfo, getDayColor, getDayName, getDayDate, getIconHref, checkWeekend, getWindColor } from '../weather_utils';

export class WeatherForTheWeek extends Component {
    static template = "weather.WeatherForTheWeek";
    static props = {
        values: Object,
    };
    setup() {
        this.label_week = ": weather for the week";
        this.days = [];
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
        this.days = nextProps.values.for_week.map((day, index) => {
            let cellClass = ['week-column'];
            checkWeekend(cellClass, day.event);
            cellClass.push(getDayColor(day.event));
            const name = getDayName(day.event);
            const date = getDayDate(day.event, index);
            return {key: day.event, class: cellClass.join(' '), name: name, date: date};
        });

        this.icons = nextProps.values.for_week.map((day) => {
            let cellClass = ['week-column'];
            checkWeekend(cellClass, day.event);
            const href = getIconHref(day.icon_num);
            return {key: day.event, class: cellClass.join(' '), href: href};
        });

        this.titlesTemp = nextProps.values.for_week.map((day, index) => {
            let cellClass = ['week-column'];
            checkWeekend(cellClass, day.event);
            let name = '';
            if (index === 0) {
                cellClass.push('overflow-td');
                name = 'Temperature, °C';
            }
            return {key: day.event, class: cellClass.join(' '), name: name};
        });

        const tempBarHeights = getTempBarsInfo(nextProps.values.for_week, true);
        this.tempBars = nextProps.values.for_week.map((day, index) => {
            let cellClass = ['week-column bar'];
            checkWeekend(cellClass, day.event);
            let topStyle = '';
            let midStyle = '';
            let botStyle = '';
            let maxTemp = '';
            let minTemp = '';
            if (index < tempBarHeights.length) {
                topStyle = `height: ${tempBarHeights[index].top}px`;
                const borderTop = `1px solid ${tempBarHeights[index].borderTop}`;
                const borderBot = `1px solid ${tempBarHeights[index].borderBot}`;
                midStyle = `height: ${tempBarHeights[index].mid}px; background-color: ${tempBarHeights[index].color}; border-top: ${borderTop}; border-bottom: ${borderBot}`;
                botStyle = `height: 10px`;
                maxTemp = tempBarHeights[index].maxTemp;
                minTemp = tempBarHeights[index].minTemp;
            }
            return {
                key: day.event,
                class: cellClass.join(' '),
                topStyle: topStyle,
                midStyle: midStyle,
                botStyle: botStyle,
                maxTemp: maxTemp,
                minTemp: minTemp,
            };
        });

        this.titlesWind = nextProps.values.for_week.map((day, index) => {
            let cellClass = ['week-column'];
            checkWeekend(cellClass, day.event);
            let name = '';
            if (index === 0) {
                cellClass.push('overflow-td');
                name = 'Wind, m/s';
            }
            return {key: day.event, class: cellClass.join(' '), name: name};
        });

        this.winds = nextProps.values.for_week.map((day) => {
            let cellClass = ['week-column day-wind'];
            checkWeekend(cellClass, day.event);
            const value = Math.round(+day.wind_speed);
            const directionStyle = `transform: rotate(${day.wind_angle}deg);`;
            const valueStyle = `color: ${getWindColor(value)}`;
            return {
                key: day.event,
                class: cellClass.join(' '),
                value: value,
                directionStyle: directionStyle,
                valueStyle: valueStyle,
            };
        });

        this.titlesPreci = nextProps.values.for_week.map((day, index) => {
            let cellClass = ['week-column'];
            checkWeekend(cellClass, day.event);
            let name = '';
            if (index === 0) {
                cellClass.push('overflow-td');
                name = 'Precipitation, mm';
            }
            return {key: day.event, class: cellClass.join(' '), name: name};
        });

        this.precipitation = [];
        if (tempBarHeights.length) {
            const maxPreci = tempBarHeights.map(x => x.precipitation).reduce(function(prev, curr) { return prev > curr ? prev : curr; });
            this.precipitation = nextProps.values.for_week.map((day) => {
                let cellClass = ['week-column day-preci'];
                checkWeekend(cellClass, day.event);
                const maxHeight = 20;
                const value = +day.prec_total;
                const color = value === 0 ? 'gray' : 'var(--rain-color)';
                const height = maxPreci === 0 ? 0 : maxHeight * value / maxPreci;
                const valueStyle = `color: ${color}`;
                const heightStyle = `height: ${height}px`;
                return {
                    key: day.event,
                    class: cellClass.join(' '),
                    value: value,
                    valueStyle: valueStyle,
                    heightStyle: heightStyle,
                };
            });
        }
    }
}
