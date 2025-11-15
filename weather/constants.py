API_WEATHER_KEY = "q4kqk4a5in0j5gtew4ih95gdqtt3hr8ripdtf68n"
API_WEATHER_TZ = "auto"
API_WEATHER_CR_URL = "https://www.meteosource.com"
API_WEATHER_CR_INFO = "Powered by Meteosource"
API_WEATHER_INFO = "https://www.gismeteo.ru/weather-zhodino-11949/10-days/"
API_WEATHER_LAT = "51.154876"
API_WEATHER_LON = "17.037135"

astro_api = 'https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted={formatted}'
find_places_prefix_api = 'https://www.meteosource.com/api/v1/free/find_places_prefix?text={text}&key={key}'
nearest_place_api = 'https://www.meteosource.com/api/v1/free/nearest_place?lat={lat}&lon={lon}&key={key}'
forecast_api = 'https://www.meteosource.com/api/v1/free/point?place_id={place_id}&sections=all&timezone={timezone}&language=en&units=auto&key={key}'

CURRENT = 'current'
FORECASTED_HOURLY = 'hourly'
FORECASTED_DAILY = 'daily'

EVENT_TYPE = [
    (CURRENT, 'Current'),
    (FORECASTED_HOURLY, 'Forecasted hourly'),
    (FORECASTED_DAILY, 'Forecasted daily'),
]
