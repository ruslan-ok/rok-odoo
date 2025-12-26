from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

TIME_AXIS_SCALES = {
    "xAxis": {
        "type": "time",
        "time": {
            "displayFormats": {
                "datetime": "MMM D, YYYY, h:mm:ss a",
                "millisecond": "h:mm:ss.SSS a",
                "second": "h:mm:ss a",
                "minute": "h:mm a",
                "hour": "MMM D, hA",
                "day": "MMM D",
                "week": "ll",
                "month": "MMM YYYY",
                "quarter": "[Q]Q - YYYY",
                "year": "YYYY",
            },
        },
    },
}


class ChartPeriod(Enum):
    p1h = "1h"
    p3h = "3h"
    p12h = "12h"
    p24h = "24h"
    p7d = "7d"
    p30d = "30d"
    p3m = "3m"
    p1y = "1y"
    p3y = "3y"
    p5y = "5y"


def monthdelta(date, delta):
    m, y = (date.month + delta) % 12, date.year + ((date.month) + delta - 1) // 12
    if not m:
        m = 12
    d = min(
        date.day,
        [
            31,
            29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ][m - 1],
    )
    return date.replace(day=d, month=m, year=y) - timedelta(1)


def yeardelta(date, delta):
    y = date.year + delta
    m = date.month
    d = min(
        date.day,
        [
            31,
            29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ][m - 1],
    )
    return date.replace(day=d, month=m, year=y) - timedelta(1)


def get_start_date(enddate: datetime, period: ChartPeriod) -> datetime:
    match period:
        case ChartPeriod.p1h:
            startdate = enddate
        case ChartPeriod.p3h:
            startdate = enddate - timedelta(hours=2)
        case ChartPeriod.p12h:
            startdate = enddate - timedelta(hours=11)
        case ChartPeriod.p24h:
            startdate = enddate
        case ChartPeriod.p7d:
            startdate = enddate - timedelta(days=6)
        case ChartPeriod.p30d:
            startdate = monthdelta(enddate, -1)
        case ChartPeriod.p3m:
            startdate = monthdelta(enddate, -3)
        case ChartPeriod.p1y:
            startdate = yeardelta(enddate, -1)
        case ChartPeriod.p3y:
            startdate = yeardelta(enddate, -3)
        case ChartPeriod.p5y:
            startdate = yeardelta(enddate, -5)
    return startdate


@dataclass
class SourceData:
    event: datetime
    value: Decimal


def get_adaptive_date_format(data: list[SourceData]) -> str:
    """
    Determine the appropriate date format based on the time span of the data.
    Returns a format string that provides good readability for the given time range.
    """
    if not data or len(data) < 2:
        return "%Y-%m-%d %H:%M:%S"

    # Get the time span
    min_time = min(item.event for item in data)
    max_time = max(item.event for item in data)
    time_span = max_time - min_time

    # Determine format based on time span
    if time_span.days <= 1:
        # Less than 1 day: show time with hours and minutes
        return "%H:%M"
    if time_span.days < 6:
        # Less than 6 days: show date and time
        return "%m-%d %H:%M"
    if time_span.days <= 30 * 6:
        # Less than 6 months: show date only
        return "%Y-%m-%d"
    # More than 6 years: show year only
    return "%Y-%m"


def approximate(data: list[SourceData], goal: int, x_label: str, y_label: str) -> list:
    chart_points = []
    x_mask = get_adaptive_date_format(data)
    cur_time = None
    average: Decimal = Decimal(0)
    qty: int = 0
    skiper = int(len(data) / goal)
    if not skiper:
        return [
            {x_label: item.event.strftime(x_mask), y_label: item.value} for item in data
        ]
    for ndx, item in enumerate(data):
        if not cur_time:
            cur_time = item.event
            average = Decimal(0)
            qty = 0
        if item.value:
            average += Decimal(item.value)
            qty += 1
        if ndx % skiper == 0 and qty:
            chart_points.append(
                {x_label: cur_time.strftime(x_mask), y_label: average / qty},
            )
            cur_time = None
    return chart_points


def build_chart_config(label: str, chart_points, rgb: str):
    dataset = {
        "label": label,
        "data": chart_points,
        "backgroundColor": f"rgba({rgb}, 0.2)",
        "borderColor": f"rgba({rgb}, 1)",
        "borderWidth": 1,
        "cubicInterpolationMode": "monotone",
    }
    chart_data = {
        "datasets": [dataset],
    }
    chart_options = {
        "plugins": {
            "legend": {
                "display": False,
            },
        },
        "elements": {
            "point": {
                "radius": 0,
            },
        },
        "scales": TIME_AXIS_SCALES,
    }
    return {
        "type": "line",
        "data": chart_data,
        "options": chart_options,
    }
