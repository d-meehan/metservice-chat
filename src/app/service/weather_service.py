import os
from datetime import datetime, timedelta, date

from loguru import logger
import httpx
from nicegui import app

from models import MetservicePointTimeRequest, MetserviceTimePointSummary, MetserviceVariable, MetservicePointTimeRequest, MetservicePeriodSummary, QueryClassification
from service.user_service import UserService
from utils.constants import QueryTypesEnum, QueryPeriodsEnum, WeatherIconMap, WeatherVarMap, query_variable_map, period_hours_map, weather_unit_map

class WeatherService:
    def __init__(self, user_service: UserService) -> None:
        self.data_store: list[MetservicePeriodSummary] = []
        self.user_service = user_service

    async def get_weather_data(self, classification: QueryClassification) -> None:
        logger.info(f"request.location: {classification.location}")
        if classification.location is None:
            classification.location = await self._get_request_location(classification)
        new_data_dates, new_data_query_types = await self._check_data_store(classification)
        if new_data_dates:
            logger.info("Conditions not met, fetching new weather data.")
            metservice_request = await self._create_API_request(request=classification, dates=new_data_dates, query_types=new_data_query_types)
            metservice_response = await self._metservice_api_call(metservice_request)
            await self._store_weather_data(metservice_response, classification)


    async def fetch_data(self, classification: QueryClassification) -> list[MetservicePeriodSummary]:
        if classification.query_period == QueryPeriodsEnum.MULTIPLE_DAYS and classification.query_to_date:
            classification_dates = await self._classify_dates(classification)
        else:
            classification_dates = [classification.query_from_date]
        
        weather_data = await self._initialise_weather_data(classification)
        logger.debug(f"Initialised weather data: {weather_data}")
        for data in self.data_store:
            if data.location != classification.location or data.date not in classification_dates:
                continue
            logger.info(f"Data found for location: {classification.location}, date: {data.date} and type: {classification.query_type}")
            
            for hour_summary in data.hour_summaries:
                if await self._matches_query_period(hour_summary, classification.query_period):
                    weather_data['time_data'].append(datetime.combine(data.date, hour_summary.hour))  
                    for variable in hour_summary.variables:
                        await self._update_weather_data(weather_data, variable)
        return weather_data
    
    async def fetch_weather_icons(self, weather_data: dict[str, list]) -> dict[str, list]:
        """
        Fetch weather icons based on the updated weather_data structure for a general weather query,
        processing the data directly from the dictionary.
        """
        temp_icon_data = []
        logger.debug(f"weather_data: {weather_data}")

        for idx, time in enumerate(weather_data['time_data']):
            # Extract weather variables for this time point by index
            prec_mm = weather_data.get(WeatherVarMap.rain, [None])[idx]
            wind_km_h = weather_data.get(WeatherVarMap.wind_speed, [None])[idx]
            cloud_pct = weather_data.get(WeatherVarMap.cloud_cover, [None])[idx]
            temp_c = weather_data.get(WeatherVarMap.temp, [None])[idx]

            # Handle missing data gracefully
            if None in (prec_mm, wind_km_h, cloud_pct, temp_c):
                logger.warning(f"Missing weather data at index {idx}; skipping classification.")
                continue

            weather_category = await self._categorise_weather(prec_mm, wind_km_h, cloud_pct, temp_c)
            logger.info(f"time: {time.time()} Category: {weather_category}")

            # Adjust classification for day or night
            if time.time() <= datetime.strptime('06:00:00', '%H:%M:%S').time() or time.time() > datetime.strptime('18:00:00', '%H:%M:%S').time():
                weather_category += '_night'
            else:
                weather_category += '_day'

            weather_icon = WeatherIconMap[weather_category].value
            temp_dict = {'x': time.timestamp() * 1000, 'y': temp_c, 'iconPath': weather_icon}
            temp_icon_data.append(temp_dict)
        weather_data[WeatherVarMap.temp] = temp_icon_data

        return weather_data

    async def _get_request_location(self, classification: QueryClassification) -> str: 
        if 'location' not in app.storage.user:
            try:
                latitude = await self.user_service.user_latitude()
                longitude = await self.user_service.user_longitude()
                app.storage.user['location'] = await self._lat_lon_to_location(latitude, longitude)
                app.storage.user['latitude'] = latitude
                app.storage.user['longitude'] = longitude
            except Exception as e:
                logger.error(f"No location provided in query and user did not respond to request for location: {e}")

        return app.storage.user['location']

    async def _categorise_weather(self, prec_mm: float, wind_km_h: float, cloud_pct: float, temp_c: float) -> str:
        try:
            if temp_c < 0 and 0 <= prec_mm <= 0.2 and wind_km_h < 40:
                return 'frost'
            elif 0 <= prec_mm <= 0.2 and wind_km_h < 40:
                if cloud_pct < 10:
                    return 'fine'
                elif cloud_pct <= 70:
                    return 'partly_cloudy'
                else:
                    return 'cloudy'
            elif 0.2 < prec_mm < 2 and wind_km_h < 40:
                return 'few_showers'
            elif 2 <= prec_mm <= 6 and wind_km_h < 40:
                return 'showers'
            elif prec_mm > 6 and wind_km_h < 40:
                return 'rain'
            elif wind_km_h >= 40:
                return 'wind'
            else:
                return 'Unspecified'
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 'Error'
    
    async def _matches_query_period(self, hour_summary: MetserviceTimePointSummary, query_periods: list[QueryPeriodsEnum]) -> bool:
        """
        Check if the hour summary matches any of the hours specified in the query periods.
        """
        hour = hour_summary.hour.hour  # Assuming hour_summary.hour is a datetime.time object
        logger.debug(f"hour: {hour}")
        for period in query_periods:
            if hour in period_hours_map.get(period, []):
                logger.debug(f"Matched period: {period}")
                return True
        return False

    async def _initialise_weather_data(self, classification: QueryClassification) -> list[MetservicePeriodSummary]:
        """
        Initialize the weather data dictionary with lists based on the query_variable_map
        and the current classification.query_types.
        """
        weather_data = {'time_data': []}  # Always include time_data
        for query_type in classification.query_type:
            for variable in query_variable_map[query_type]:
                if variable not in weather_data:
                    weather_data[variable] = []
        return weather_data
    
    async def _update_weather_data(self, weather_data: dict[str, list], variable: MetserviceVariable):
        """
        Update the weather data dictionary with the variable value.
        """

        if WeatherVarMap(variable.name) in weather_data:
            weather_data[WeatherVarMap(variable.name)].append(variable.value)
    
    async def _check_data_store(self, classification: QueryClassification) -> tuple[list[date], set[str]]:
        if classification.query_period == QueryPeriodsEnum.MULTIPLE_DAYS and classification.query_to_date:
            classification_dates = await self._classify_dates(classification)
        else:
            classification_dates = [classification.query_from_date]


        dates_missing_data = []
        unique_missing_query_types = set()

        # Check data availability
        for date in classification_dates:
            date_has_all_data = True
            for query_type in classification.query_type:
                query_type_present = False

                for stored_data in self.data_store:
                    logger.debug(f"Stored data location: {stored_data.location}, classification location: {classification.location} stored date: {stored_data.date}, classification date: {classification.query_from_date} stored period_types: {stored_data.period_types}, classification period_types: {classification.query_period}, stored weather_data_types: {stored_data.weather_data_types}, classification data_types: {classification.query_type}")
                    if stored_data.location == classification.location and stored_data.date == date and (stored_data.period_types == classification.query_period or QueryPeriodsEnum.WHOLE_DAY in stored_data.period_types):
                        if query_type in stored_data.weather_data_types or \
                                (query_type not in [QueryTypesEnum.GENERAL_WEATHER, QueryTypesEnum.SEA_BOAT_SURF_FISHING] and QueryTypesEnum.GENERAL_WEATHER in stored_data.weather_data_types):
                            query_type_present = True
                            break

                if not query_type_present:
                    date_has_all_data = False
                    unique_missing_query_types.add(query_type)

            if not date_has_all_data:
                dates_missing_data.append(date)

        # Request data if any is missing
        if dates_missing_data:
            logger.info(f"Dates missing data: {dates_missing_data}")
            logger.info(f"Unique missing query types: {unique_missing_query_types}")
        return dates_missing_data, unique_missing_query_types
        
    async def _classify_dates(self, classification: QueryClassification) -> list[date]:
        delta = classification.query_to_date - classification.query_from_date
        classification_dates = [classification.query_from_date +
                                timedelta(days=i) for i in range(delta.days + 1)]
        return classification_dates

    async def _store_weather_data(self, metservice_response: list[MetservicePeriodSummary], classification: QueryClassification) -> None:
        for data in metservice_response:
            logger.debug(f"Data: {data}")
            data.location = classification.location
            data.weather_data_types = classification.query_type
            data.period_types = classification.query_period
            logger.info(f"Processing data for date: {data.date}, location: {data.location} and periods: {data.period_types}.")
            entries_to_remove = []
            data_matched = False
            for i, stored_data in enumerate(self.data_store):
                if stored_data.date == data.date and stored_data.location == data.location:
                    logger.info(f"Found existing data for date: { \
                                data.date} and location: {data.location}.")
                    if (
                        (
                            QueryTypesEnum.GENERAL_WEATHER in data.weather_data_types and
                            QueryTypesEnum.SEA_BOAT_SURF_FISHING not in stored_data.weather_data_types and
                            (
                                data.period_types == stored_data.period_types or
                                QueryPeriodsEnum.WHOLE_DAY in data.period_types
                            ) 
                        ) or
                        (
                            (
                                (
                                    QueryTypesEnum.GENERAL_WEATHER in data.weather_data_types and
                                    QueryTypesEnum.SEA_BOAT_SURF_FISHING not in stored_data.weather_data_types 
                                ) or
                            data.weather_data_types == stored_data.weather_data_types
                            ) and
                            QueryPeriodsEnum.WHOLE_DAY in data.period_types
                        )
                    ):
                        logger.info(f"Replacing existing data with data for date: { \
                                    data.date} and location: {data.location}.")
                        entries_to_remove.append(i)

                    if entries_to_remove:
                        # Reverse indices_to_remove to avoid altering list during removal
                        for i in sorted(entries_to_remove, reverse=True):
                            del self.data_store[i]
                        logger.info(f"Replacing existing data with 'whole day' data for date: { \
                                    data.date} and location: {data.location}.")
                        self.data_store.append(data)
                        continue  # Skip to the next iteration of the outer loop

                        # Conditions for combining the data
                    else:
                        for period in data.period_types:
                            if period in stored_data.period_types \
                            and (
                                QueryTypesEnum.GENERAL_WEATHER not in data.weather_data_types \
                                or QueryTypesEnum.SEA_BOAT_SURF_FISHING in stored_data.weather_data_types
                                ):
                                logger.info(f"Combining data entries for date: { \
                                            data.date}, location: {data.location} and period(s): {data.period_types}.")
                                stored_data.weather_data_types = list(
                                    set(data.weather_data_types + stored_data.weather_data_types))
                                # Assuming you want to combine these as well
                                stored_data.hour_summaries = list(
                                    set(data.hour_summaries + stored_data.hour_summaries))
                                data_matched = True
                                break
            logger.debug(f"Data matched: {data_matched}")
            if not data_matched:
                logger.info(f"Appending new data for date: { \
                            data.date} and location: {data.location}.")
                self.data_store.append(data)  # Append the new data

    async def _create_API_request(self, request: QueryClassification, dates: list[date], query_types: set[str]) -> MetservicePointTimeRequest:
        logger.info(f"Request: {request}")
        start_time = min(min(time) for period, time in period_hours_map.items() if period in request.query_period)
        first_date = dates[0]
        last_date = dates[-1]
        from_datetime = datetime(year=first_date.year, month=first_date.month,day=first_date.day,hour=start_time).strftime("%Y-%m-%dT%H:00:00Z")
        if request.query_period == [QueryPeriodsEnum.MULTIPLE_DAYS]:
            days = (last_date-first_date).days
            repeat = days * 4 - 1
            interval = "6h"
        elif request.query_period == [QueryPeriodsEnum.WHOLE_DAY]:
            repeat = 23
            interval = "1h"
        else:
            repeat = len(request.query_period)*5
            interval = "1h"
        logger.info(f"From datetime: {from_datetime}, interval: {interval}, repeat: {repeat}")
        variables = []
        for query_type in query_types:
            variables.extend(query_variable_map[query_type])
        latitude, longitude = await self._location_to_lat_lon(request.location)

        metservice_request = MetservicePointTimeRequest(
            latitude=latitude,
            longitude=longitude,
            variables=variables,
            from_datetime=from_datetime,
            interval=interval,
            repeat=repeat
        )

        return metservice_request

    @staticmethod
    async def _location_to_lat_lon(location: str) -> tuple[float, float]:
        logger.info(f"Location: {location}")
        
        async with httpx.AsyncClient() as request_client:
            geocode_response = await request_client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": location,
                    "key": os.environ["GOOGLE_MAPS_API_KEY"]
                }
            )

        if geocode_response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {geocode_response.status_code}"
            )
        geocode_response = geocode_response.json()
        latitude=geocode_response['results'][0]['geometry']['location']['lat']
        longitude=geocode_response['results'][0]['geometry']['location']['lng']

        return latitude, longitude

    
    @staticmethod
    async def _lat_lon_to_location(latitude: float, longitude: float) -> str:
        async with httpx.AsyncClient() as request_client:
            geocode_response = await request_client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "latlng": f"{latitude},{longitude}",
                    "key": os.environ["GOOGLE_MAPS_API_KEY"],
                    "result_type": "political"
                }
            )

        if geocode_response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {geocode_response.status_code}"
            )
        geocode_response = geocode_response.json()
        location = geocode_response['results'][0]['formatted_address']

        return location

    async def _metservice_api_call(self, request: MetservicePointTimeRequest) -> list[MetservicePeriodSummary]:
        logger.info(f"Request: {request}")
        async with httpx.AsyncClient() as request_client:
            response = await request_client.post(
                "https://forecast-v2.metoceanapi.com/point/time",
                headers={"x-api-key": os.environ["METSERVICE_KEY"]},
                json={
                    "points": [{
                        "lon": request.longitude,
                        "lat": request.latitude,
                    }],
                    "variables": request.variables,
                    "time": {
                        "from": request.from_datetime,
                        "interval": request.interval,
                        "repeat": request.repeat
                    }
                }
            )

        if response.status_code != 200:
            raise ValueError(f"Request failed with status code {response.status_code}")
        logger.info(f"API response: {response.json()}")

        metservice_response = await self._clean_metservice_response(response)
        return metservice_response

    async def _clean_metservice_response(self, metservice_api_response: httpx.Response) -> list[MetservicePeriodSummary]:
        response_json = metservice_api_response.json()
        metservice_response: list[MetservicePeriodSummary] = []

        try:
            points_data: list[dict] = response_json['dimensions']['point']['data']
            times_data: list[str] = response_json['dimensions']['time']['data']
            variables_data: dict = response_json['variables']
        except KeyError as e:
            logger.info(f"Missing key in response: {e}")
            return []

        for point in points_data:
            latitude = point.get('lat')
            longitude = point.get('lon')

            # Group times by day
            times_by_day: dict[str, list[str]] = {}
            for time in times_data:
                day = time.split('T')[0]
                if day not in times_by_day:
                    times_by_day[day] = []
                times_by_day[day].append(time)

            for day, day_times in times_by_day.items():
                hour_summaries = []

                for time in day_times:
                    hour_str = time.split('T')[1][:5]
                    hour = datetime.strptime(f"{day} {hour_str}", "%Y-%m-%d %H:%M").time()
                    variables = []

                    for var_name, var_data in variables_data.items():
                        index = times_data.index(time)
                        var_value = var_data['data'][index]
                        var_units = var_data.get('units')

                        # Apply transformations based on units
                        if var_units in weather_unit_map:
                            transform_func, var_units = weather_unit_map[var_units]
                            var_value = transform_func(var_value)
                        var_value = round(var_value, 2)
                        variables.append(MetserviceVariable(name=var_name, value=var_value, units=var_units))

                    hour_summaries.append(MetserviceTimePointSummary(hour=hour, variables=variables))

                if hour_summaries:
                    metservice_response.append(MetservicePeriodSummary(
                        weather_data_types=[],
                        period_types=[],
                        date=datetime.strptime(day, "%Y-%m-%d"),
                        latitude=latitude,
                        longitude=longitude,
                        hour_summaries=hour_summaries
                    ))
                logger.debug(f"metservice_response: {metservice_response}")
        return metservice_response