from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

TIME_AXIS_SCALES = {
    "xAxis": {
        "type": "time",
        "time": {
            "displayFormats": {
                "datetime": "MMM d, yyyy, h:mm:ss a",
                "millisecond": "h:mm:ss.SSS a",
                "second": "h:mm:ss a",
                "minute": "h:mm a",
                "hour": "MMM d, ha",
                "day": "MMM d",
                "week": "ll",
                "month": "MMM yyyy",
                "quarter": "[Q]Q - yyyy",
                "year": "yyyy",
            },
        },
    },
}


@dataclass
class SourceData:
    event: datetime
    value: Decimal


def approximate(data: list[SourceData], goal: int) -> list:
    chart_points = []
    x_mask = "%Y-%m-%d %H:%M:%S"
    cur_time = None
    average: Decimal = Decimal(0)
    qty: int = 0
    skiper = int(len(data) / goal)
    if not skiper:
        return [{"x": item.event.strftime(x_mask), "y": item.value} for item in data]
    for ndx, item in enumerate(data):
        if not cur_time:
            cur_time = item.event
            average = Decimal(0)
            qty = 0
        if item.value:
            average += Decimal(item.value)
            qty += 1
        if ndx % skiper == 0 and qty:
            chart_points.append({"x": cur_time.strftime(x_mask), "y": average / qty})
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
