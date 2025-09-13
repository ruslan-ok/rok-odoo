from odoo import models, fields, api
from decimal import Decimal
import requests
from datetime import datetime
from .delta import approximate, SourceData


API_COIN_RATE = "https://api.coinranking.com/v2/coin/Qwsogvtv82FCd/"


class RokFinanceBtcPriceLive(models.Model):
    _name = 'rok.finance.btc_price_live'
    _description = 'BTC price (live)'
    _auto = False  # virtual, no table

    timestamp = fields.Datetime(readonly=True)
    price = fields.Float(readonly=True, aggregator='avg')

    @api.model
    def _parse_domain_period(self, domain):
        """Map a timestamp domain to coinranking timePeriod string."""
        start = end = None
        for leaf in domain or []:
            if isinstance(leaf, (list, tuple)) and len(leaf) == 3 and leaf[0] == 'timestamp':
                op = leaf[1]
                val = leaf[2]
                try:
                    # Odoo passes UTC strings
                    if isinstance(val, str):
                        val_dt = fields.Datetime.from_string(val)
                    else:
                        val_dt = val
                except Exception:
                    continue
                if op in ('>=', '>'):
                    start = val_dt
                elif op in ('<=', '<'):
                    end = val_dt
        if not start or not end:
            return None, None, '7d'
        delta_days = max(1, (end - start).days)
        if delta_days <= 7:
            return start, end, '7d'
        if delta_days <= 30:
            return start, end, '30d'
        if delta_days <= 90:
            return start, end, '3m'
        if delta_days <= 365:
            return start, end, '1y'
        if delta_days <= 3 * 365:
            return start, end, '3y'
        return start, end, '5y'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """Provide grouped series from external API to power odoo_line charts.
        Supports groupby on 'timestamp:day'.
        """
        _, _, period = self._parse_domain_period(domain)
        api_key = self.env['ir.config_parameter'].sudo().get_param('rok_finance.coinranking_api_key')
        if not api_key:
            return []
        headers = {'x-access-token': api_key, 'User-Agent': 'Mozilla/5.0'}
        url = f"{API_COIN_RATE}history?timePeriod={period}"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get('status') != 'success':
            return []
        history = payload.get('data', {}).get('history', [])
        src_data = []
        for i in reversed(range(len(history))):
            h = history[i]
            sd = SourceData(event=datetime.utcfromtimestamp(h['timestamp']), value=Decimal(h['price'] if h['price'] else prev))
            src_data.append(sd)
            prev = sd.value
        chart_points = approximate(src_data, 100, 'timestamp:day', 'price')
        return chart_points
