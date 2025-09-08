from odoo import models, fields, api
import requests
from datetime import datetime


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
        start, end, period = self._parse_domain_period(domain)
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
        history = payload['data']['history']
        # Bucket by day
        buckets = {}
        for h in history:
            ts_ms = h.get('timestamp')
            # coinranking returns ms; fallback if seconds
            ts_sec = int(ts_ms) // 1000 if int(ts_ms) > 10**12 else int(ts_ms)
            dt = datetime.utcfromtimestamp(ts_sec)
            if start and dt < start:
                continue
            if end and dt > end:
                continue
            key = dt.strftime('%Y-%m-%d 00:00:00')
            price = h.get('price')
            if price is None:
                continue
            buckets.setdefault(key, {'sum': 0.0, 'count': 0})
            buckets[key]['sum'] += float(price)
            buckets[key]['count'] += 1

        results = []
        for day_key in sorted(buckets.keys()):
            s = buckets[day_key]
            avg_price = s['sum'] / max(1, s['count'])
            row = {
                'timestamp:day': day_key,
                'price': avg_price,
                '__count': s['count'],
            }
            results.append(row)
        return results


