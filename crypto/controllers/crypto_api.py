import json
import os
import requests
from datetime import datetime, timezone
from decimal import Decimal
from dotenv import load_dotenv

from odoo import http, fields

from ..constants import ChartPeriod
from odoo.addons.rok_apps.tools.utils import approximate, build_chart_config, SourceData


class CryptoError(Exception):
    pass


class CryptoController(http.Controller):
    @http.route("/crypto/data", type="json", auth="public", methods=["POST"])
    def get_crypto(self, period: str) -> dict:
        try:
            period = ChartPeriod(period)
            ret = self.get_crypto_data(period)
            return {"result": "ok", "data": ret}
        except CryptoError as inst:
            proc, info = inst.args
            return {"result": "error", "procedure": proc, "info": info}

    def get_crypto_data(self, period: ChartPeriod):
        load_dotenv()
        chart_points = []
        current = change = amount = None
        api_url = os.getenv("API_COIN_RATE")
        api_key = os.getenv("API_COIN_RATE_KEY")
        if api_url and api_key:
            headers = {"x-access-token": api_key, "User-Agent": "Mozilla/5.0"}
            # timePeriod: 1h 3h 12h 24h 7d 30d 3m 1y 3y 5y
            resp = requests.get(api_url + "history?timePeriod=" + period.value, headers=headers)
            prev = 0
            if resp.status_code == 200:
                ret = json.loads(resp.content)
                if ret["status"] == "success":
                    current = float(ret["data"]["history"][0]["price"])
                    change = float(ret["data"]["change"])
                    amount = 0.07767845 * current
                    src_data = []
                    for i in reversed(range(len(ret["data"]["history"]))):
                        h = ret["data"]["history"][i]
                        event = datetime.fromtimestamp(h["timestamp"], tz=timezone.utc)
                        value = Decimal(h["price"] if h["price"] else prev)
                        sd = SourceData(event=event, value=value)
                        src_data.append(sd)
                        prev = sd.value
                    chart_points = approximate(src_data, 200)

        chart_config = build_chart_config("BTC/USD", chart_points, "111, 184, 71")
        create_vals = [
            {"dt": fields.Datetime.from_string(point["x"]), "value": point["y"]}
            for point in chart_points
        ]
        http.request.env["rok.crypto"].sudo().search([]).unlink()
        http.request.env["rok.crypto"].sudo().create(create_vals)
        widget_data = {
            "chart": chart_config,
            "current": current,
            "change": change,
            "amount": amount,
            "price_url": os.getenv("API_COIN_INFO"),
            "amount_url": f"{os.getenv("API_WALLET")}{os.getenv("API_WALLET_KEY")}",
        }
        return widget_data
