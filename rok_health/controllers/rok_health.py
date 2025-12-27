from datetime import datetime, timedelta

from odoo import fields, http

from ..constants import ChartPeriod
from odoo.addons.rok_apps.tools.utils import SourceData, approximate, build_chart_config


class HealthError(Exception):
    pass


class HealthController(http.Controller):
    @http.route("/anthropometry/data", type="json", auth="public", methods=["POST"])
    def get_anthropometry(self, period: str) -> dict:
        try:
            period = ChartPeriod(period)
            ret = self.get_anthropometry_data(period)
            return {"result": "ok", "data": ret}
        except HealthError as inst:
            return {
                "result": "error",
                "info": inst.args[0] if inst.args else "Unknown error",
            }

    def get_anthropometry_data(self, period: ChartPeriod):
        env = http.request.env
        match period:
            case ChartPeriod.p1w:
                domain = [("measurement", ">=", datetime.now() - timedelta(days=7))]
            case ChartPeriod.p1m:
                domain = [("measurement", ">=", datetime.now() - timedelta(days=30))]
            case ChartPeriod.p3m:
                domain = [("measurement", ">=", datetime.now() - timedelta(days=90))]
            case ChartPeriod.p1y:
                domain = [("measurement", ">=", datetime.now() - timedelta(days=365))]
            case ChartPeriod.p3y:
                domain = [
                    ("measurement", ">=", datetime.now() - timedelta(days=365 * 3)),
                ]
            case ChartPeriod.p10y:
                domain = [
                    ("measurement", ">=", datetime.now() - timedelta(days=365 * 10)),
                ]
        data = env["rok.health.anthropometry"].search(domain, order="measurement")
        if not data:
            raise HealthError(f"No data found for period {period.value}")
        src_data = [
            SourceData(event=x.measurement, value=x.weight)
            for x in data
            if x.measurement and x.weight
        ]
        chart_points = approximate(src_data, 200)
        last = src_data[-1].value
        first = src_data[0].value
        trend = (last - first) / first * 100 if first else 0
        chart_config = build_chart_config("Weight", chart_points, "60, 90, 210")
        return {
            "chart_data": chart_config,
            "current": last,
            "trend": trend,
        }

    @http.route("/anthropometry/add", type="json", auth="public", methods=["POST"])
    def add_anthropometry(self, value: float) -> dict:
        try:
            env = http.request.env
            env["rok.health.anthropometry"].create(
                {
                    "weight": value,
                    "measurement": fields.Datetime.now(),
                    "user_id": http.request.env.user.id,
                },
            )
            return {"result": "ok"}
        except HealthError as inst:
            return {
                "result": "error",
                "info": inst.args[0] if inst.args else "Unknown error",
            }
