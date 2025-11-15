/** @odoo-module **/

import { windSpeedColors, temperatureColors } from './colors';

const barColorGradient = [[0xff, 0xc5, 0xbf], [0xf0, 0xf4, 0xc1], [0xbf, 0xd9, 0xff]];
const barColorOpacity = 0.5;
const borderColorGradient = [[0xfd, 0x9e, 0x93], [0xcc, 0xee, 0x95], [0xa0, 0xc6, 0xff]];
const borderColorOpacity = 1;


function getTempColor(temperature, border) {
    const roundedTemp = Math.round(temperature).toString();
    if (roundedTemp in temperatureColors) {
        // @ts-ignore
        const color = temperatureColors[roundedTemp];
        return color;
    }

    let colorHot, colorZero, colorCold, opacity;
    if (border) {
        colorHot = borderColorGradient[0];
        colorZero = borderColorGradient[1];
        colorCold = borderColorGradient[2];
        opacity = borderColorOpacity;
    } else {
        colorHot = barColorGradient[0];
        colorZero = barColorGradient[1];
        colorCold = barColorGradient[2];
        opacity = barColorOpacity;
    }
    let rgb;
    if (temperature === 0)
        rgb = colorZero;
    else {
        let colorTemp, weight;
        if (temperature > 0) {
            colorTemp = colorHot;
            weight = 35 - (temperature > 35 ? 35 : temperature);
        } else {
            colorTemp = colorCold;
            weight = 35 + (temperature < -35 ? -35 : temperature);
        }
        const w1 = weight / 35;
        var w2 = 1 - w1;
        rgb = [
            Math.round(colorZero[0] * w1 + colorTemp[0] * w2),
            Math.round(colorZero[1] * w1 + colorTemp[1] * w2),
            Math.round(colorZero[2] * w1 + colorTemp[2] * w2)
        ];
    }
    return 'rgba(' + rgb[0] + ', ' + rgb[1] + ', ' + rgb[2] + ', ' + opacity + ')';
}

export class TempBarHeight {
    maxTemp = '';
    minTemp = '';
    avgTemp = '';
    top = 0;
    mid = 0;
    color = '';
    borderTop = '';
    borderBot = '';
    precipitation = 0;
}

export function getTempBarsInfo(values, forWeek) {
    let ret = [];
    if (!values.length) {
        return ret;
    }
    let maxPeriodValue;
    let minPeriodValue, barHeight;
    if (forWeek) {
        maxPeriodValue = values.map((x) => +x.temperature_max).reduce(function (prev, curr) { return prev > curr ? prev : curr; });
        minPeriodValue = values.map((x) => +x.temperature_min).reduce(function (prev, curr) { return prev < curr ? prev : curr; });
    }
    else {
        maxPeriodValue = values.map((x) => +x.temperature).reduce(function (prev, curr) { return prev > curr ? prev : curr; });
        minPeriodValue = values.map((x) => +x.temperature).reduce(function (prev, curr) { return prev < curr ? prev : curr; });
        barHeight = Math.round(maxPeriodValue - minPeriodValue) * 4;
    }
    ret = values.map((day) => {
        let maxValue, maxValueStr, minValue, minValueStr, avgValue, avgValueStr, topHeight, midHeight, borderTopColor, borderBotColor;
        if (forWeek) {
            maxValue = Math.round(+day.temperature_max);
            maxValueStr = (maxValue === 0 ? '' : (maxValue > 0 ? '+' : '')) + maxValue;
            minValue = Math.round(+day.temperature_min);
            minValueStr = (minValue === 0 ? '' : (minValue > 0 ? '+' : '')) + minValue;
            topHeight = 15 + Math.round(maxPeriodValue - day.temperature_max) * 2;
            midHeight = 2 * (day.temperature_max - day.temperature_min);
            borderTopColor = getTempColor(day.temperature_max, true);
            borderBotColor = getTempColor(day.temperature_min, true);
        } else {
            avgValue = Math.round(+day.temperature);
            avgValueStr = (avgValue === 0 ? '' : (avgValue > 0 ? '+' : '')) + avgValue;
            topHeight = 5 + (maxPeriodValue - day.temperature) * 4;
            midHeight = barHeight;
            borderTopColor = getTempColor(day.temperature, true);
            borderBotColor = getTempColor(day.temperature, true);
        }

        return {
            maxTemp: maxValueStr,
            minTemp: minValueStr,
            avgTemp: avgValueStr,
            top: topHeight,
            mid: midHeight,
            color: getTempColor(day.temperature, false),
            borderTop: borderTopColor,
            borderBot: borderBotColor,
            precipitation: day.prec_total,
        }
    });
    return ret;
}

export function getIconHref(num) {
    return `/weather/static/src/img/${num}.svg`
}

export function getDayColor(dayDate) {
    const dt = new Date(dayDate);
    const day = dt.getDay();
    let color = 'blue';
    if (day === 0 || day === 6) {
        color = 'red';
    }
    return color;
}

export function getDayName(dayDate) {
    const dt = new Date(dayDate);
    let ret = '??';
    switch (dt.getDay()) {
        case 0: ret = 'Sun'; break;
        case 1: ret = 'Mon'; break;
        case 2: ret = 'Tue'; break;
        case 3: ret = 'Wed'; break;
        case 4: ret = 'Thu'; break;
        case 5: ret = 'Fri'; break;
        case 6: ret = 'Sat'; break;
    }
    return ret;
}

export function getMonthName(month) {
    let ret = '???';
    switch (month) {
        case 0: ret = 'Jan'; break;
        case 1: ret = 'Feb'; break;
        case 2: ret = 'Mar'; break;
        case 3: ret = 'Apr'; break;
        case 4: ret = 'May'; break;
        case 5: ret = 'Jun'; break;
        case 6: ret = 'Jul'; break;
        case 7: ret = 'Aug'; break;
        case 8: ret = 'Sep'; break;
        case 9: ret = 'Oct'; break;
        case 10: ret = 'Nov'; break;
        case 11: ret = 'Dec'; break;
    }
    return ret;
}

export function getDayDate(dayDate, index) {
    const dt = new Date(dayDate);
    const day = dt.getDate();
    let ret = day.toString();
    if (day === 1 || index === 0) {
        const month = dt.getMonth();
        ret += ' ' + getMonthName(month);
    }
    return ret;
}

export function getHourNum(dayDate, correct=0) {
    const dt = new Date(dayDate);
    let hour = dt.getHours() - correct;
    if (hour < 0) {
        hour = 23;
    }
    if (hour > 23) {
        hour = 0;
    }
    return hour;
}

export function getHourName(dayDate) {
    let hr = getHourNum(dayDate);
    return hr.toString();
}

export function checkNight(cellClass, event, correct, sunrise, sunset) {
    const hour = getHourNum(event, correct);
    if (hour > sunset || hour < sunrise) {
        cellClass.push('night');
    }
    if (hour === sunset || hour === sunrise) {
        cellClass.push('twilight');
    }
}

export function checkWeekend(cellClass, event) {
    const dt = new Date(event);
    const day = dt.getDay();
    if (day === 0 || day === 6) {
        cellClass.push('weekend');
    }
}

export function getWindColor(value) {
    const sValue = Math.round(value).toString();
    if (sValue in windSpeedColors) {
        // @ts-ignore
        const color = windSpeedColors[sValue];
        return color;
    }
    return '#000';
}

export function pickUpImage(event, sunrise, sunset, cloud_cover) {
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