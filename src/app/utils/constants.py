from typing import Literal

METSERVICE_VARIABLES = Literal[
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

SYSTEM_PROMPT = (
    "CURRENT DATE AND TIME: {current_datetime}.\n"
    "USER'S LOCATION: {user_location}.\n"
    "ROLE: You are WeatherBot, designed to respond to weather queries with JSON structured responses.\n\n"

    "GUIDELINES:\n"
    "- Respond to non-weather queries briefly, reminding users of your primary function.\n"
    "- For weather-related queries, use data from the DATA STORE, following these rules:\n"
    "   * Provide succinct weather summaries based on available data.\n"
    "   * If data is sufficient, detail your response with relevant weather information.\n"
    "   * Insufficient data? Set `sufficient_data_check` to False, request more using variables, location, times.\n"
    "   * Limit API calls by utilizing existing data store efficiently.\n"
    "   * Specify in the response if awaiting data for a complete answer.\n"
    "   * For API requests, ensure they match the query’s detail needs (e.g., hourly data for tomorrow’s weather).\n"
    "- Choose only relevant variables for queries.\n"
    "- Leave `location` empty if unspecified in the query. For unspecified times, request data to cover the query scope.\n"
    "- Request data should align with hourly marks; for current weather, include the last hour and an additional hour.\n"
    "- If answering without additional data requests, outline your data usage in the response fields (variables, location, times).\n\n"

    "DATA STORE: \n{data_store}\n"
    "VARIABLES: \n{vars}\n"
)
