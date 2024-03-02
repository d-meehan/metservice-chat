import os
from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel
from loguru import logger
from nicegui import app
import instructor
import googlemaps
from dotenv import load_dotenv
import openai

from models import QueryClassification
from utils.constants import ClassificationPrompt, QueryResponsePrompt
from presentation.ui_manager import UIManager
from service.weather_service import WeatherService

load_dotenv()

pydantic_client = instructor.apatch(openai.AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY']))
client = openai.AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])
gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)

class ChatService:
    def __init__(self, weather_service: WeatherService, ui_manager: UIManager) -> None:
        self.weather_service = weather_service
        self.ui_manager = ui_manager

    async def classify_query(self, query: str) -> QueryClassification:
        self.ui_manager.toggle_visual_processing(show_spinner=True)
        self.ui_manager.add_message(
                role="user",
                content=query,
                )
        classification: QueryClassification = await self._classify_query(response_model=QueryClassification)
        if classification.location == []:
            if 'location' not in app.storage.user:
                try:
                    latitude = await self.weather_service.user_service.user_latitude()
                    longitude = await self.weather_service.user_service.user_longitude()
                    app.storage.user['latitude'] = latitude
                    app.storage.user['longitude'] = longitude
                    app.storage.user['location'] = await self.weather_service._lat_lon_to_location(latitude, longitude)
                except Exception as e:
                    logger.error(
                        f"No location provided in query and user did not respond to request for location: {e}")
            classification.location = app.storage.user['location']
        return classification


    async def process_message(self) -> None:
        response = await self._answer_query()
        self.ui_manager.add_message(
                role="WeatherBot",
                content=response,
                )
        self.ui_manager.toggle_visual_processing(show_spinner=False)


    async def _classify_query(self, response_model: QueryClassification) -> QueryClassification:
        """
        This function takes the user's message, the chat log, the data store, the response model and the app storage as input and returns the response from the GPT model.
        
        Parameters:
        user_message (str): The user's message
        chat_log (list[Message]): The chat log
        data_store (list[list[MetserviceTimePointSummary]]): The data store
        response_model (BaseModel): The response model
        app_storage (dict): The app storage
        """

        system_prompt = ClassificationPrompt.format(
            current_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
            ]
        chat_log = self.ui_manager.chat_log

        for message in chat_log:
            if message.role == "WeatherBot":
                messages.append({"role": "assistant", "content": message.content})
            else:
                messages.append({"role": message.role, "content": message.content})
        while messages[-1].get("role") == "assistant":
            messages.pop()
        logger.info(f"Messages: {messages}")

        response = await pydantic_client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_model=response_model,
            messages=messages,
        )

        assert isinstance(response, QueryClassification)
        logger.info(f"GPT response: {response}")
        return response
    
    async def _answer_query(self) -> str:
        """
        This function takes the user's message, the chat log, the data store, the response model and the app storage as input and returns the response from the GPT model.
        
        Parameters:
        user_message (str): The user's message
        chat_log (list[Message]): The chat log
        data_store (list[list[MetserviceTimePointSummary]]): The data store
        response_model (BaseModel): The response model
        app_storage (dict): The app storage
        """

        formatted_data = [
            f"Date: {data.date}, Query type(s): {data.weather_data_types}, Location: {data.location}, Period(s): {data.period_types}  \n {
                '\n\n'.join(
                    f'Time: {time.hour} \n {'\n'.join(f'{variable.name}: {variable.value}{variable.units}' for variable in time.variables)}' for time in data.hour_summaries)}"
            for data in self.weather_service.data_store
        ]
        formatted_data = "\n\n".join(formatted_data)

        if 'location' in app.storage.user:
            location = app.storage.user['location']
        else:
            location = "unknown location"

        system_prompt = QueryResponsePrompt.format(
            current_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            user_location=location,
            data_store=formatted_data,
        )

        messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
            ]
        chat_log = self.ui_manager.chat_log

        for message in chat_log:
            if message.role == "WeatherBot":
                messages.append({"role": "assistant", "content": message.content})
            else:
                messages.append({"role": message.role, "content": message.content})
        while messages[-1].get("role") == "assistant":
            messages.pop()
        logger.info(f"Messages: {messages}")

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
        )

        logger.info(f"GPT response: {response}")
        return response.choices[0].message.content