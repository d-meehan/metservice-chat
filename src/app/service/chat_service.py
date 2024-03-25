import os
from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel
from loguru import logger
from nicegui import app
import instructor
from dotenv import load_dotenv
import openai

from models import QueryClassification
from utils.constants import ClassificationPrompt, QueryResponsePrompt
from presentation.ui_manager import UIManager
from service.weather_service import WeatherService
from service.user_service import UserService

load_dotenv()

pydantic_client = instructor.apatch(openai.AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY']))
client = openai.AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)

class ChatService:
    """
    This class is responsible for classifying a query to allow the weather service to fetch the appropriate data.
    It then generates a response to the query with the context of the available data.
    """
    def __init__(self, weather_service: WeatherService, ui_manager: UIManager, user_service: UserService) -> None:
        self.weather_service = weather_service
        self.ui_manager = ui_manager
        self.user_service = user_service

    async def classify_query(self, query: str) -> QueryClassification:
        """
        This function takes the user's query as input and returns the classification of the query based on the included response_model.
        
        Parameters:
        query (str): The user's query
        
        Returns:
        QueryClassification: The classification of the query
        """

        await self.ui_manager.toggle_visual_processing(show_spinner=True)
        await self.ui_manager.add_message(
                role="user",
                content=query,
                )
        classification: QueryClassification = await self._model_query_classification(response_model=QueryClassification)
        if classification.location == None and classification.query_type != "non-weather":
            while 'location' not in app.storage.user or app.storage.user['location'] in [None, "null"]:
                try:
                    latitude = await self.user_service.user_latitude()
                    longitude = await self.user_service.user_longitude()
                    logger.info(f"User location: {latitude}, {longitude}")
                    app.storage.user['latitude'] = latitude
                    app.storage.user['longitude'] = longitude

                    location = await self.weather_service._lat_lon_to_location(latitude=latitude, longitude=longitude)
                    app.storage.user['location'] = location
                except Exception as e:
                    logger.error(
                        f"No location provided in query and user did not respond to request for location: {e}")
            classification.location = app.storage.user['location']
        return classification


    async def process_message(self) -> None:
        """
        This function takes the user's message, the chat log, the data store, the response model and the app storage as input and returns the response from the GPT model.
        """
        formatted_data = await self._format_data_store()
        if 'location' in app.storage.user:
            location = app.storage.user['location']
        else:
            location = "unknown location"
        
        system_prompt = QueryResponsePrompt.format(
            current_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            user_location=location,
            data_store=formatted_data,
        )

        messages = await self._format_chat_log(system_prompt=system_prompt)
        
        model_response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        response = model_response.choices[0].message.content

        await self.ui_manager.add_message(
                role="WeatherBot",
                content=response,
                )
        
        await self.ui_manager.toggle_visual_processing(show_spinner=False)


    async def _model_query_classification(self, response_model: QueryClassification) -> QueryClassification:
        system_prompt = ClassificationPrompt.format(
            current_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        messages = await self._format_chat_log(system_prompt=system_prompt)

        response = await pydantic_client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_model=response_model,
            messages=messages,
        )

        assert isinstance(response, QueryClassification)
        logger.info(f"GPT response: {response}")
        return response
    
    async def _format_data_store(self) -> str:
        data_store = self.weather_service.data_store
        formatted_data = [
            f"Date: {data.date}, Query type(s): {data.weather_data_types}, Location: {data.location}, Period(s): {data.period_types}  \n {
                '\n\n'.join(
                    f'Time: {time.hour} \n {'\n'.join(f'{variable.name}: {variable.value}{variable.units}' for variable in time.variables)}' for time in data.hour_summaries)}"
            for data in data_store
        ]
        formatted_data = "\n\n".join(formatted_data)
        return formatted_data

    async def _format_chat_log(self, system_prompt: str) -> list[dict[str, str]]:
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
        return messages

