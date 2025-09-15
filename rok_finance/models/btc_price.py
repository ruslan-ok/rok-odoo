from odoo import models, fields, api
from decimal import Decimal
import requests
from datetime import datetime, timezone, timedelta
from odoo.addons.rok_spreadsheet.utils.delta import approximate, SourceData


API_COIN_RATE = "https://api.coinranking.com/v2/coin/Qwsogvtv82FCd/"


class RokFinanceBtcPrice(models.Model):
    _name = 'rok.finance.btc_price'
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
            sd = SourceData(event=datetime.fromtimestamp(h['timestamp'], tz=timezone.utc), value=Decimal(h['price'] if h['price'] else prev))
            src_data.append(sd)
            prev = sd.value
        chart_points = approximate(src_data, 100, 'timestamp:day', 'price')
        return chart_points


class RokFinanceBtcKpi(models.Model):
    _name = 'rok.finance.btc_kpi'
    _description = 'BTC KPI data'
    _auto = False  # virtual, no table

    current_price = fields.Float(readonly=True)
    period_start_price = fields.Float(readonly=True)
    price_change_percent = fields.Float(readonly=True)

    @api.model
    def search_read(self, domain, fields, offset=0, limit=None, order=None):
        """Return KPI data as search_read format."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('rok_finance.coinranking_api_key')
        if not api_key:
            return []

        headers = {'x-access-token': api_key, 'User-Agent': 'Mozilla/5.0'}
        # Get historical data for comparison
        history_url = f"{API_COIN_RATE}history?timePeriod=7d"
        history_resp = requests.get(history_url, headers=headers, timeout=15)
        history_resp.raise_for_status()
        history_payload = history_resp.json()

        period_start_price = current_price = price_change_percent = 0
        if history_payload.get('status') == 'success':
            history = history_payload.get('data', {}).get('history', [])
            if history:
                current_price = float(history[0].get('price', 0))
                period_start_price = float(history[-1].get('price', 0))
                price_change_percent = ((current_price - period_start_price) / period_start_price * 100) if period_start_price > 0 else 0

        # Return in search_read format with virtual ID
        record = {'id': 1}  # Virtual ID for spreadsheet compatibility

        # Only include requested fields
        if not fields or 'current_price' in fields:
            record['current_price'] = current_price
        if not fields or 'period_start_price' in fields:
            record['period_start_price'] = period_start_price
        if not fields or 'price_change_percent' in fields:
            record['price_change_percent'] = price_change_percent

        return [record]

    @api.model
    @api.readonly
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        """Return KPI data as web_search_read format."""
        fields = list(specification.keys()) if specification else ['current_price', 'period_start_price', 'price_change_percent']
        records = self.search_read(domain, fields, offset, limit, order)

        # Format for web_search_read - must return dict with 'length' and 'records'
        return {
            'length': len(records),
            'records': records
        }
