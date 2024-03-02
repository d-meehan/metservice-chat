from enum import Enum

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

class QueryTypesEnum(Enum):
    NON_WEATHER = 'non-weather'
    GENERAL_WEATHER = 'general weather'
    TEMPERATURE = 'temperature'
    RAIN = 'rain'
    CLOUD ='cloud'
    WIND = 'wind'
    SEA_BOAT_SURF_FISHING = 'sea, boat, surf and fishing'

class QueryPeriodsEnum(Enum):
    MORNING = 'morning'
    AFTERNOON = 'afternoon'
    EVENING = 'evening'
    NIGHT = 'night'
    WHOLE_DAY = 'whole day'
    MULTIPLE_DAYS = 'multi-day'

weather_unit_map = {
    "degreeK": (lambda x: x - 273.15, "C"),
    "meterPerSecond": (lambda x: x * 3.6, "km/h"),
    "percent": (lambda x: x, "%"),
    "millimeterPerHour": (lambda x: x, "mm/h"),
}

class WeatherVarMap(Enum):
    humidity = 'air.humidity.at-2m'
    temp = 'air.temperature.at-2m'
    cloud_cover = 'cloud.cover'
    rain = 'precipitation.rate'
    wind_direction = 'wind.direction.at-10m'
    wind_speed = 'wind.speed.at-10m'
    sea_temperature = 'sea.temperature.at-surface'
    wave_height = 'wave.height'
    wave_height_max = 'wave.height.max'
    wave_direction_mean = 'wave.direction.mean'
    wave_direction_peak = 'wave.direction.peak'
    wave_period_peak = 'wave.period.peak'
    wind_speed_gust = 'wind.speed.gust.at-10m'

query_variable_map = {
    QueryTypesEnum.GENERAL_WEATHER: [
        WeatherVarMap.humidity,
        WeatherVarMap.temp,
        WeatherVarMap.cloud_cover,
        WeatherVarMap.rain,
        WeatherVarMap.wind_direction,
        WeatherVarMap.wind_speed,
    ],
    QueryTypesEnum.TEMPERATURE: [
        WeatherVarMap.temp,
    ],
    QueryTypesEnum.RAIN: [
        WeatherVarMap.rain,
    ],
    QueryTypesEnum.CLOUD: [
        WeatherVarMap.cloud_cover,
    ],
    QueryTypesEnum.WIND: [
        WeatherVarMap.wind_direction,
        WeatherVarMap.wind_speed,
    ],
    QueryTypesEnum.SEA_BOAT_SURF_FISHING: [
        WeatherVarMap.sea_temperature,
        WeatherVarMap.wave_height,
        WeatherVarMap.wave_height_max,
        WeatherVarMap.wave_direction_mean,
        WeatherVarMap.wave_direction_peak,
        WeatherVarMap.wave_period_peak,
        WeatherVarMap.wind_speed,
        WeatherVarMap.wind_speed_gust,
        WeatherVarMap.wind_direction,
    ],
}


period_hours_map = {
    QueryPeriodsEnum.MORNING: list(range(6, 12)),  # 5AM to 11AM
    QueryPeriodsEnum.AFTERNOON: list(range(12, 18)),  # 12PM to 4PM
    QueryPeriodsEnum.EVENING: list(range(18, 24)),  # 5PM to 8PM
    QueryPeriodsEnum.NIGHT: list(range(0, 6)),  # 9PM to 4AM
    QueryPeriodsEnum.WHOLE_DAY: list(range(0, 24)),  # Whole day
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
    wind_day = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/wind.svg'
    wind_night = 'https://cdn.jsdelivr.net/gh/Makin-Things/weather-icons/animated/wind.svg'