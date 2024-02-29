import os
from datetime import datetime
from loguru import logger
import httpx
from nicegui import app
from models import MetservicePointTimeRequest, MetserviceTimePointSummary, MetserviceVariable, MetservicePointTimeRequest, MetservicePeriodSummary, QueryClassification
from service.user_service import UserService
from utils.constants import query_variable_map, query_time_map

class WeatherService:
    def __init__(self, user_service: UserService) -> None:
        self.data_store: list[MetservicePeriodSummary] = []
        self.user_service = user_service

    async def get_weather_data(self, classification: QueryClassification) -> None:
        while not any(
            (
                (
                    classification.query_type == stored_data.weather_data_type or
                    classification.query_type not in ["general weather", "sea, boat, surf and fishing"] and
                    stored_data.weather_data_type != "general weather"
                ) and
                (
                    classification.query_period == stored_data.period_type or
                    stored_data.period_type in ["whole_day", "multi-day"]
                ) and
                classification.location == stored_data.location and
                classification.query_from_date == stored_data.date
            )
            for stored_data in self.data_store
        ):
            logger.info("Conditions not met, fetching new weather data.")
            metservice_request = await self._create_API_request(classification)
            metservice_response = await self._metservice_api_call(metservice_request)
        
        if metservice_response:
            await self._store_weather_data(metservice_response, classification)

    async def _store_weather_data(self, metservice_response: list[MetservicePeriodSummary], classification: QueryClassification) -> None:
        for data in metservice_response:
            data.location = classification.location
            data.weather_data_type = classification.query_type
            data.period_type = classification.query_period
            if not any(
                stored_data.date == data.date and 
                stored_data.location == data.location and
                stored_data.weather_data_type == data.weather_data_type and
                stored_data.hour_summaries == hour_summary 
                for stored_data in self.data_store for hour_summary in data.hour_summaries):
                self.data_store.append(data)
            else:
                logger.info(f"Data already exists for time: {data.date}, latitude: {data.latitude}, longitude: {data.longitude}")

    async def _create_API_request(self, request: QueryClassification) -> MetservicePointTimeRequest:
        logger.info(f"Request: {request}")
        start_time = min(
            time for period, time in query_time_map.items() if period in request.query_period)
        from_datetime = datetime.combine(request.query_from_date, start_time.time()).strftime("%Y-%m-%dT%H:00:00Z")
        if request.query_period == ["multi-day"]:
            days = (request.query_to_date - request.query_from_date).days
            repeat = days * 4
            interval = "6h"
        elif request.query_period == ["whole day"]:
            repeat = 24
            interval = "1h"
        else:
            repeat = len(request.query_period)*6
            interval = "1h"
        logger.info(f"From datetime: {from_datetime}, interval: {interval}, repeat: {repeat}")
        variables = []
        for query_type in request.query_type:
            variables.extend(query_variable_map[query_type])

        logger.info(f"request.location: {request.location}")
        if request.location is None:
            if 'location' not in app.storage.user:
                try:
                    latitude = await self.user_service.user_latitude()
                    longitude = await self.user_service.user_longitude()
                    app.storage.user['location'] = await self._lat_lon_to_location(latitude, longitude)
                except Exception as e:
                    logger.error(f"No location provided in query and user did not respond to request for location: {e}")
            request.location = app.storage.user['location']

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
                        if var_units == "degreeK":
                            var_value -= 273.15
                            var_units = "C"
                        if var_units == "meterPerSecond":
                            var_value *= 3.6
                            var_units = "km/h"
                        if var_units == "percent":
                            var_units = "%"
                        if var_units == "millimeterPerHour":
                            var_units = "mm/h"
                        logger.info(f"Variable: {var_name}, Value: {var_value}, Units: {var_units}")
                        var_value = round(var_value, 2)
                        variables.append(MetserviceVariable(name=var_name, value=var_value, units=var_units))

                    hour_summaries.append(MetserviceTimePointSummary(hour=hour, variables=variables))

                if hour_summaries:
                    metservice_response.append(MetservicePeriodSummary(
                        weather_data_type=[],
                        date=datetime.strptime(day, "%Y-%m-%d"),
                        latitude=latitude,
                        longitude=longitude,
                        hour_summaries=hour_summaries
                    ))

        return metservice_response