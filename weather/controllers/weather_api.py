import json
from datetime import datetime, timedelta
from dateutil import tz
from dataclasses import dataclass, field
from decimal import Decimal
import requests

from odoo import http

from ..constants import (
    API_WEATHER_KEY, API_WEATHER_TZ, API_WEATHER_CR_URL, API_WEATHER_INFO,
    CURRENT, FORECASTED_DAILY, FORECASTED_HOURLY, find_places_prefix_api, nearest_place_api, astro_api, forecast_api
)


class WeatherError(Exception):
    pass


class WeatherController(http.Controller):
    @http.route('/weather/data', type='json', auth='user')
    def get_weather(self, location: str=None, lat: str=None, lon: str=None) -> dict:
        try:
            ret = self.get_db_chart_data(location, lat, lon)
            return {'result': 'ok', 'data': ret}
        except WeatherError as inst:
            proc, info = inst.args
            return {'result': 'error', 'procedure': proc, 'info': info}

    def get_db_chart_data(self, location: str, lat: str, lon: str) -> dict:
        place = self.get_place(location, lat, lon)
        lifetime = datetime.now() - timedelta(hours=2)
        env = http.request.env
        forecast = env["weather.forecast"].search([('place_id', '=', place.id), ('fixed', '>', lifetime)], order='event')
        astro = self.get_astro(place)
        if not len(forecast):
            self.get_forecast_api_data(place)
            forecast = env["weather.forecast"].search([('place_id', '=', place.id), ('fixed', '>', lifetime)], order='event')
        ret = self.get_forecast_data(place, forecast, astro)
        return ret

    def get_place(self, location: str, lat: str, lon: str):
        env = http.request.env
        if location:
            place = env["weather.place"].search([('name', '=', location)], limit=1)
            if place:
                return place
            headers = {'accept': 'application/json'}
            token = API_WEATHER_KEY
            url = find_places_prefix_api.replace('{text}', location).replace('{key}', token)
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                raise WeatherError('get_place', f'(1) Bad response status code: {resp.status_code}')
            ret = json.loads(resp.content)
            if type(ret) == list:
                if len(ret) > 1:
                    tmp = [x for x in ret if x['country'] in ('Republic of Belarus', 'Poland')]
                    if len(tmp) > 0:
                        ret = tmp[0]
            if type(ret) == list and len(ret) > 0:
                ret = ret[0]
            if type(ret) != dict:
                raise WeatherError('get_place', f'Wrong type of response data: {ret}')
            place = env["weather.place"].create({
                'place_id': ret['place_id'],
                'name': ret['name'],
                'adm_area1': ret['adm_area1'],
                'adm_area2': ret['adm_area2'] if ret['adm_area2'] else '',
                'country': ret['country'],
                'lat': ret['lat'],
                'lon': ret['lon'],
                'timezone': ret['timezone'],
                'type': ret['type'],
                'search_name': location,
                'lat_cut': '',
                'lon_cut': '',
            })
            return place

        if not lat or not lon:
            raise WeatherError('get_place', 'Empty parameters "location", "lat", "lon".')

        lat_cut = lat[:5] + '00000'
        lon_cut = lon[:5] + '00000'
        place = env["weather.place"].search([('lat_cut', '=', lat_cut), ('lon_cut', '=', lon_cut)], limit=1)
        if place:
            return place
        headers = {'accept': 'application/json'}
        token = API_WEATHER_KEY
        url = nearest_place_api.replace('{lat}', lat).replace('{lon}', lon).replace('{key}', token)
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise WeatherError('get_place', f'(2) Bad response status code: {resp.status_code}')
        ret = json.loads(resp.content)
        place = env["weather.place"].create({
            'place_id': ret['place_id'],
            'name': ret['name'],
            'adm_area1': ret['adm_area1'],
            'adm_area2': ret['adm_area2'] if ret['adm_area2'] else '',
            'country': ret['country'],
            'lat': ret['lat'],
            'lon': ret['lon'],
            'timezone': ret['timezone'],
            'type': ret['type'],
            'search_name': '',
            'lat_cut': lat_cut,
            'lon_cut': lon_cut,
        })
        return place

    def get_astro(self, place):
        date = datetime.now().date()
        env = http.request.env
        astro = env["weather.astro"].search([('place_id', '=', place.id), ('date', '=', date)], limit=1)
        if astro:
            return astro
        headers = {'accept': 'application/json'}
        url = astro_api.replace('{lat}', place.lat).replace('{lon}', place.lon).replace('{formatted}', '0')
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise WeatherError('get_astro', f'(2) Bad response status code: {resp.status_code}')
        ret = json.loads(resp.content)
        if ret['status'] != 'OK':
            raise WeatherError('get_astro', f'(2) Bad status in API data: {ret}')

        sunrise = self.get_datetime_value(ret, 'sunrise', place.timezone)
        sunset = self.get_datetime_value(ret, 'sunset', place.timezone)
        solar_noon = self.get_datetime_value(ret, 'solar_noon', place.timezone)
        civil_twilight_begin = self.get_datetime_value(ret, 'civil_twilight_begin', place.timezone)
        civil_twilight_end = self.get_datetime_value(ret, 'civil_twilight_end', place.timezone)
        nautical_twilight_begin = self.get_datetime_value(ret, 'nautical_twilight_begin', place.timezone)
        nautical_twilight_end = self.get_datetime_value(ret, 'nautical_twilight_end', place.timezone)
        astronomical_twilight_begin = self.get_datetime_value(ret, 'astronomical_twilight_begin', place.timezone)
        astronomical_twilight_end = self.get_datetime_value(ret, 'astronomical_twilight_end', place.timezone)

        astro = env["weather.astro"].create({
            'place_id': place.id,
            'date': date,
            'day_length': ret['results']['day_length'],
            'sunrise': sunrise,
            'sunset': sunset,
            'solar_noon': solar_noon,
            'civil_twilight_begin': civil_twilight_begin,
            'civil_twilight_end': civil_twilight_end,
            'nautical_twilight_begin': nautical_twilight_begin,
            'nautical_twilight_end': nautical_twilight_end,
            'astronomical_twilight_begin': astronomical_twilight_begin,
            'astronomical_twilight_end': astronomical_twilight_end,
        })
        return astro

    def get_datetime_value(self, data: dict, field_name: str, timezone: str) -> datetime:
        value = data['results'][field_name]
        if '+' in value:
            tz_part = value.split('+')[1]
            if tz_part != '00:00':
                raise WeatherError('get_datetime_value', 'Expected datetime value with timezone 00:00. Got: ' + value)
            utc = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')
            to_zone = tz.gettz(timezone)
            local = utc.astimezone(to_zone)
            s_local = local.strftime('%Y-%m-%dT%H:%M:%S')
            ret = datetime.strptime(s_local, '%Y-%m-%dT%H:%M:%S')
            return ret
        ret = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        return ret

    def get_forecast_api_data(self, place) -> None:
        env = http.request.env
        headers = {'accept': 'application/json'}
        token = API_WEATHER_KEY
        timezone = API_WEATHER_TZ
        url = forecast_api.replace('{place_id}', place.place_id).replace('{timezone}', timezone).replace('{key}', token)
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise WeatherError('get_forecast_api_data', f'Bad response status code: {resp.status_code}')
        ret = json.loads(resp.content)
        fixed = datetime.now().replace(second=0, microsecond=0)
        try:
            weather = env["weather.forecast"].create({
                'place_id': place.id,
                'event': fixed,
                'fixed': fixed,
                'ev_type': CURRENT,
                'lat': ret['lat'],
                'lon': ret['lon'],
                'elevation': ret['elevation'],
                'timezone': ret['timezone'],
                'units': ret['units'],
                'weather': ret['current']['icon'],
                'icon': ret['current']['icon_num'],
                'summary': ret['current']['summary'],
                'temperature': ret['current']['temperature'],
                'wind_speed': ret['current']['wind']['speed'],
                'wind_angle': ret['current']['wind']['angle'],
                'wind_dir': ret['current']['wind']['dir'],
                'prec_total': ret['current']['precipitation']['total'],
                'prec_type': ret['current']['precipitation']['type'],
                'cloud_cover': ret['current']['cloud_cover'],
            })
            for hour in ret['hourly']['data']:
                env["weather.forecast"].create({
                    'place_id': place.id,
                    'event': datetime.strptime(hour['date'], '%Y-%m-%dT%H:%M:%S'),
                    'fixed': fixed,
                    'ev_type': FORECASTED_HOURLY,
                    'lat': ret['lat'],
                    'lon': ret['lon'],
                    'elevation': weather.elevation,
                    'timezone': weather.timezone,
                    'units': weather.units,
                    'weather': hour['weather'],
                    'icon': hour['icon'],
                    'summary': hour['summary'],
                    'temperature': hour['temperature'],
                    'temperature_min': None,
                    'temperature_max': None,
                    'wind_speed': hour['wind']['speed'],
                    'wind_angle': hour['wind']['angle'],
                    'wind_dir': hour['wind']['dir'],
                    'prec_total': hour['precipitation']['total'],
                    'prec_type': hour['precipitation']['type'],
                    'cloud_cover': hour['cloud_cover']['total'],
                })

            for day in ret['daily']['data']:
                env["weather.forecast"].create({
                    'place_id': place.id,
                    'event': datetime.strptime(day['day'], '%Y-%m-%d'),
                    'fixed': fixed,
                    'ev_type': FORECASTED_DAILY,
                    'lat': ret['lat'],
                    'lon': ret['lon'],
                    'elevation': weather.elevation,
                    'timezone': weather.timezone,
                    'units': weather.units,
                    'weather': day['weather'],
                    'icon': day['icon'],
                    'summary': day['summary'],
                    'temperature': day['all_day']['temperature'],
                    'temperature_min': day['all_day']['temperature_min'],
                    'temperature_max': day['all_day']['temperature_max'],
                    'wind_speed': day['all_day']['wind']['speed'],
                    'wind_angle': day['all_day']['wind']['angle'],
                    'wind_dir': day['all_day']['wind']['dir'],
                    'prec_total': day['all_day']['precipitation']['total'],
                    'prec_type': day['all_day']['precipitation']['type'],
                    'cloud_cover': day['all_day']['cloud_cover']['total'],
                })
        except Exception as ex:
            raise WeatherError('get_forecast_api_data', f'Exception: {str(ex)}, {ret=}')

    def get_forecast_data(self, place, forecast, astro) -> dict:
        currents = forecast.filtered(lambda x: x.ev_type == CURRENT)
        for_day = forecast.filtered(lambda x: x.ev_type == FORECASTED_HOURLY)
        for_week = forecast.filtered(lambda x: x.ev_type == FORECASTED_DAILY)
        if not len(currents):
            raise WeatherError('get_forecast_data', 'Empty forecast Queryset.')
        if not astro.sunrise or not astro.sunset:
            raise WeatherError('get_forecast_data', 'Empty AstroData values.')
        current = DayWeather(
            event=currents[0].event,
            state=currents[0].weather,
            summary=currents[0].summary,
            icon_num=currents[0].icon,
            temperature=currents[0].temperature,
            temperature_min=currents[0].temperature_min,
            temperature_max=currents[0].temperature_max,
            wind_speed=currents[0].wind_speed,
            wind_dir=currents[0].wind_dir,
            wind_angle=currents[0].wind_angle,
            cloud_cover=currents[0].cloud_cover,
            prec_total=currents[0].prec_total,
            prec_type=currents[0].prec_type,
        )
        data = PeriodWeather(
            lat=currents[0].lat,
            lon=currents[0].lon,
            place=place.name,
            sunrise=astro.sunrise,
            sunset=astro.sunset,
            elevation=currents[0].elevation,
            timezone=currents[0].timezone,
            units=currents[0].units,
            cr_url=API_WEATHER_CR_URL,
            #cr_info=f'forecast_len={len(forecast)}, currents_len={len(currents)}, for_day_len={len(for_day)}, for_week_len={len(for_week)}, {debug_info}',
            cr_info=API_WEATHER_INFO,
            current=current,
        )
        for x in for_day:
                data.for_day.append(DayWeather(
                    event=x.event,
                    state=x.weather,
                    summary=x.summary,
                    icon_num=x.icon,
                    temperature=x.temperature,
                    temperature_min=x.temperature_min,
                    temperature_max=x.temperature_max,
                    wind_speed=x.wind_speed,
                    wind_dir=x.wind_dir,
                    wind_angle=x.wind_angle,
                    cloud_cover=x.cloud_cover,
                    prec_total=x.prec_total,
                    prec_type=x.prec_type,
                ))
        for x in for_week:
                data.for_week.append(DayWeather(
                    event=x.event,
                    state=x.weather,
                    summary=x.summary,
                    icon_num=x.icon,
                    temperature=x.temperature,
                    temperature_min=x.temperature_min,
                    temperature_max=x.temperature_max,
                    wind_speed=x.wind_speed,
                    wind_dir=x.wind_dir,
                    wind_angle=x.wind_angle,
                    cloud_cover=x.cloud_cover,
                    prec_total=x.prec_total,
                    prec_type=x.prec_type,
                ))
        ret = data.to_json()
        return ret


@dataclass
class DayWeather:
    event: datetime
    state: str
    summary: str
    icon_num: int
    temperature: Decimal
    temperature_min: Decimal | None
    temperature_max: Decimal | None
    wind_speed: Decimal
    wind_dir: str
    wind_angle: int
    cloud_cover: int
    prec_total: Decimal
    prec_type: str

    def to_json(self):
        return {
            "event": self.event.strftime('%Y-%m-%dT%H:%M:%S'),
            "state": self.state,
            "summary": self.summary,
            "icon_num": self.icon_num,
            "temperature": '{0:.1f}'.format(self.temperature),
            "temperature_min": '{0:.1f}'.format(self.temperature_min) if self.temperature_min else None,
            "temperature_max": '{0:.1f}'.format(self.temperature_max) if self.temperature_max else None,
            "wind_speed": '{0:.1f}'.format(self.wind_speed),
            "wind_dir": self.wind_dir,
            "wind_angle": self.wind_angle,
            "cloud_cover": self.cloud_cover,
            "prec_total": '{0:.1f}'.format(self.prec_total),
            "prec_type": self.prec_type,
        }

@dataclass
class PeriodWeather:
    lat: str
    lon: str
    place: str
    elevation: int
    timezone: str
    units: str
    cr_url: str
    cr_info: str
    sunrise: datetime
    sunset: datetime
    current: DayWeather
    for_day: list[DayWeather] = field(default_factory=list)
    for_week: list[DayWeather] = field(default_factory=list)

    def to_json(self):
        return {
            "lat": self.lat,
            "lon": self.lon,
            "place": self.place,
            "elevation": self.elevation,
            "timezone": self.timezone,
            "units": self.units,
            "cr_url": self.cr_url,
            "cr_info": self.cr_info,
            "sunrise": self.sunrise.strftime('%Y-%m-%d %H:%M'),
            "sunset": self.sunset.strftime('%Y-%m-%d %H:%M'),
            "current": self.current.to_json(),
            "for_day": [x.to_json() for x in self.for_day],
            "for_week": [x.to_json() for x in self.for_week],
        }
