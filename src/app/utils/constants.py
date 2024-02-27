from typing import Literal
from enum import Enum
from datetime import datetime

MetserviceVariables = Literal[
    'air.humidity.at-2m',
    'air.pressure.at-sea-level',
    'air.temperature.at-2m',
    'air.visibility',
    'atmosphere.convective.potential.energy',
    'cloud.base.height',
    'cloud.cover',
    'precipitation.rate',
    'radiation.flux.downward.longwave',
    'radiation.flux.downward.shortwave',
    'wind.direction.at-10m',
    'wind.direction.at-100m',
    'wind.speed.at-10m',
    'wind.speed.at-100m',
    'wind.speed.eastward.at-100m',
    'wind.speed.eastward.at-10m',
    'wind.speed.gust.at-10m',
    'wind.speed.northward.at-100m',
    'wind.speed.northward.at-10m',
    'wave.height',
    'wave.height.max',
    'wave.direction.peak',
    'wave.period.peak',
    'wave.height.above-8s',
    'wave.height.below-8s',
    'wave.period.above-8s.peak',
    'wave.period.below-8s.peak',
    'wave.direction.above-8s.peak',
    'wave.direction.below-8s.peak',
    'wave.direction.mean',
    'wave.directional-spread',
    'wave.period.tm01.mean',
    'wave.period.tm02.mean',
    'current.speed.eastward.at-sea-surface',
    'current.speed.eastward.at-sea-surface-no-tide',
    'current.speed.eastward.barotropic',
    'current.speed.eastward.barotropic-no-tide',
    'current.speed.northward.at-sea-surface',
    'current.speed.northward.at-sea-surface-no-tide',
    'current.speed.northward.barotropic',
    'current.speed.northward.barotropic-no-tide',
    'sea.temperature.at-surface',
    'sea.temperature.at-surface-anomaly',
]

ClassificationPrompt = (
    "CURRENT DATE AND TIME: {current_datetime}.\n"
    "ROLE: Your role is to classify the user query so that we can request the right data.\n\n"

    "GUIDELINES:\n"
    "- You can only request data ten days in the future and seven days in the past.\n"
    "- Leave `location` empty if one is not specified in the query and the user is not referring to a previously stated location, we'll get the user's location.\n"
    "- Consider the context of the conversation when classifying the query, especially when it comes to query_from_date and location because the user's query may relate to something they've said previously.\n"
)

QueryResponsePrompt = (
    "CURRENT DATE AND TIME: {current_datetime}.\n"
    "USER'S LOCATION: {user_location}.\n"
    "ROLE: You are WeatherBot, designed to respond to weather queries using only data provided to you.\n\n"

    "GUIDELINES:\n"
    "- Respond to non-weather queries briefly, reminding users of your primary function.\n"
    "- Provide succinct weather summaries based only on available data.\n"

    "DATA STORE: \n{data_store}\n\n"
)

QueryTypes = Literal['non-weather', 'general weather', 'temperature',
                      'rain', 'cloud', 'wind', 'sea, boat, surf and fishing']
QueryPeriods = Literal['morning', 'afternoon',
                        'evening', 'night', 'whole day', 'multi-day']

query_variable_map = {
    'general weather': [
        'air.humidity.at-2m',
        'air.temperature.at-2m',
        'cloud.cover',
        'precipitation.rate',
        'wind.direction.at-10m',
        'wind.speed.at-10m',
    ],
    'temperature': [
        'air.temperature.at-2m',
    ],
    'rain': [
        'precipitation.rate',
    ],
    'cloud': [
        'cloud.cover',
    ],
    'wind': [
        'wind.direction.at-10m',
        'wind.speed.at-10m',
    ],
    'sea, boat, surf and fishing': [
        'sea.temperature.at-surface',
        'wave.height',
        'wave.height.max',
        'wave.direction.mean',
        'wave.direction.peak',
        'wave.period.peak',
        'wind.speed.at-10m',
        'wind.speed.gust.at-10m',
        'wind.direction.at-10m',
    ],
}

query_time_map = {
    'morning': datetime.strptime('06:00:00', '%H:00:00'),
    'afternoon': datetime.strptime('12:00:00', '%H:00:00'),
    'evening': datetime.strptime('18:00:00', '%H:00:00'),
    'night': datetime.strptime('00:00:00', '%H:00:00'),
    'whole day': datetime.strptime('00:00:00', '%H:00:00'),
    'multi-day': datetime.strptime('00:00:00', '%H:00:00'),
}


class WeatherIconMap(Enum):
    frost_day = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/frost-day.svg'
    frost_night = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/frost-night.svg'
    fine_day = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/clear-day.svg'
    fine_night = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/clear-night.svg'
    partly_cloudy_day = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/cloudy-1-day.svg'
    partly_cloudy_night = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/cloudy-1-night.svg'
    cloudy_day = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/cloudy.svg'
    cloudy_night = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/cloudy.svg'
    few_showers_day = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/rainy-1-day.svg'
    few_showers_night = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/rainy-1-night.svg'
    showers_day = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/rainy-2-day.svg'
    showers_night = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/rainy-2-night.svg'
    rain_day = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/rainy-3-day.svg'
    rain_night = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/rainy-3-night.svg'
    wind = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/wind.svg'