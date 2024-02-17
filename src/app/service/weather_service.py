import os
from loguru import logger
import httpx
from nicegui import app
from ..models import MetservicePointTimeRequest, MetserviceTimePointSummary, MetserviceVariable, MetservicePointTimeRequest, ModelResponseToWeatherQuery
from ..service.user_service import UserService

class WeatherService:
    def __init__(self, user_service: UserService) -> None:
        self.data_store: list[MetserviceTimePointSummary] = []
        self.user_service = user_service

    async def get_weather_data(self, request: ModelResponseToWeatherQuery) -> None:
        if not request.location:
            if 'latitude' not in app.storage.user and 'longitude' not in app.storage.user:
                try:
                    user_location = await self.user_service.get_user_location()
                    app.storage.user['latitude'] = user_location['latitude']
                    app.storage.user['longitude'] = user_location['longitude']
                except Exception as e:
                    logger.error(f"No location provided in query and user did not respond to request for location: {e}")
                    #TODO: create a response to the user to ask for location and adjust to appropriate error
                    return

            metservice_request = MetservicePointTimeRequest(
                latitude=app.storage.user['latitude'],
                longitude=app.storage.user['longitude'],
                variables=request.variables,
                from_datetime=request.from_datetime,
                interval=request.interval,
                repeat=request.repeat
            )
        else:
            metservice_request = await self._location_to_lat_lon(request)

        metservice_response = await self._metservice_api_call(metservice_request)
        for data in self.data_store:
            for new_data in metservice_response:
                if new_data.latitude == data.latitude and new_data.longitude == data.longitude and new_data.time == data.time:
                    metservice_response.remove(new_data)
        self.data_store.extend(metservice_response)

    async def _location_to_lat_lon(self, response: ModelResponseToWeatherQuery) -> MetservicePointTimeRequest:
        logger.info(f"Location: {response.location}")
        async with httpx.AsyncClient() as request_client:
            geocode_response = await request_client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": response.location,
                    "key": os.environ["GOOGLE_MAPS_API_KEY"]
                }
            )

        if geocode_response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {geocode_response.status_code}"
            )
        geocode_response = geocode_response.json()

        metservice_request = MetservicePointTimeRequest(
            latitude=geocode_response['results'][0]['geometry']['location']['lat'],
            longitude=geocode_response['results'][0]['geometry']['location']['lng'],
            variables=response.variables,
            from_datetime=response.from_datetime,
            interval=response.interval,
            repeat=response.repeat
        )

        return metservice_request

    async def _metservice_api_call(self, request: MetservicePointTimeRequest) -> list[MetserviceTimePointSummary]:
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
        metservice_response = []
        for point in response.json()['dimensions']['point']['data']:
            for time in response.json()['dimensions']['time']['data']:
                variables = []
                for var_name, var_data in response.json()['variables'].items():
                    var_units = var_data.get('units')
                    var_value = round(var_data.get('data')[len(metservice_response)],2)
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
                    variable = MetserviceVariable(name=var_name, value=var_value, units=var_units)
                    variables.append(variable)
                metservice_response.append(MetserviceTimePointSummary(
                    time=time, latitude=point.get('lat'), longitude=point.get('lon'), variables=variables))
        return metservice_response
