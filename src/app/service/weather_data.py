import os
from loguru import logger
import httpx
from nicegui import app
from ..schema import MetservicePointTimeRequest, GPTResponseToWeatherQuery, MetserviceTimePointSummary, MetserviceVariable

async def get_weather_data(response: GPTResponseToWeatherQuery, data_store: list[list[MetserviceTimePointSummary]]) -> list[list[MetserviceTimePointSummary]]:
    if 'latitude' not in app.storage.user and 'longitude' not in app.storage.user:
        metservice_request = await _location_to_lat_lon(response)
    else:
        metservice_request = MetservicePointTimeRequest(
            latitude=app.storage.user['latitude'],
            longitude=app.storage.user['longitude'],
            variables=response.variables,
            from_datetime=response.from_datetime,
            interval=response.interval,
            repeat=response.repeat
        )
    metservice_response = await _metservice_api_call(metservice_request)
    data_store.append(metservice_response)
    return data_store

async def _location_to_lat_lon(response: GPTResponseToWeatherQuery) -> MetservicePointTimeRequest:
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


async def _metservice_api_call(request: MetservicePointTimeRequest) -> list[MetserviceTimePointSummary]:
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
                variable = MetserviceVariable(name=var_name, units=var_data.get(
                    'units'), value=var_data.get('data')[len(metservice_response)])
                if variable.units == "degreeK":
                    variable.value -= 273.15
                    variable.units = "C"
                if variable.units == "metresPerSecond":
                    variable.units = "km/h"
                    variable.value *= 3.6
                variables.append(variable)
            metservice_response.append(MetserviceTimePointSummary(
                time=time, latitude=point.get('lat'), longitude=point.get('lon'), variables=variables))
    return metservice_response
