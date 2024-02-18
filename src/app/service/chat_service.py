import os
from datetime import datetime
from pydantic import BaseModel
from loguru import logger
from nicegui import app, ui
import instructor
import googlemaps
from dotenv import load_dotenv
import openai
from ..models import ModelResponseToWeatherQuery, Message, MetserviceTimePointSummary, MetservicePointTimeRequest
from ..utils.constants import METSERVICE_VARIABLES, SYSTEM_PROMPT
from ..presentation.ui_manager import ChatUIManager
from ..service.weather_service import WeatherService

load_dotenv()

pydantic_client = instructor.apatch(openai.AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY']))
client = openai.AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])
gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

class ChatService:
    def __init__(self, weather_service: WeatherService, chat_ui_manager: ChatUIManager) -> None:
        self.weather_service = weather_service
        self.chat_ui_manager = chat_ui_manager

    async def process_message(self, user_message: str) -> ModelResponseToWeatherQuery:
        self.chat_ui_manager.add_message_to_log(
            Message(
                role="user", 
                content=user_message,
                stamp=datetime.now().strftime("%H:%M"), 
                avatar="", 
                sent=True
                )
            )

        response: ModelResponseToWeatherQuery = await self._model_query(response_model=ModelResponseToWeatherQuery)

        self.chat_ui_manager.add_message_to_log(
            Message(
                role="assistant", 
                content=response.response, 
                stamp=datetime.now().strftime("%H:%M"), 
                avatar="", 
                sent=False
                )
            )
        while response.weather_query_check and not response.sufficient_data_check:
            await self.weather_service.get_weather_data(response)
            response = await self._model_query(response_model=ModelResponseToWeatherQuery)
            if response.sufficient_data_check:
                self.chat_ui_manager.add_message_to_log(
                    Message(
                        role="assistant", 
                        content=response.response, 
                        stamp=datetime.now().strftime("%H:%M"), 
                        avatar="", 
                        sent=False
                        )
                    )
                return response
        return response


    async def _model_query(self, response_model: BaseModel) -> ModelResponseToWeatherQuery:
        """
        This function takes the user's message, the chat log, the data store, the response model and the app storage as input and returns the response from the GPT model.
        
        Parameters:
        user_message (str): The user's message
        chat_log (list[Message]): The chat log
        data_store (list[list[MetserviceTimePointSummary]]): The data store
        response_model (BaseModel): The response model
        app_storage (dict): The app storage
        """

        if self.weather_service.data_store:
            formatted_data = [
                f"Time: {data.time}, Location: {data.location}, Latitude: {data.latitude}, Longitude: {data.longitude}  \n {
                    ', '.join([f'{variable.name}: {variable.value}{variable.units}' for variable in data.variables])}"
                for data in self.weather_service.data_store
            ]
            formatted_data = "\n\n".join(formatted_data)
        else:
            formatted_data = "No data has been requested yet."

        if 'location' not in app.storage.user:
            app.storage.user['location'] = "unknown"

        system_prompt = SYSTEM_PROMPT.format(
            current_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            user_location=app.storage.user["location"],
            data_store=formatted_data,
            vars=METSERVICE_VARIABLES
        )

        messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
            ]
        chat_log = self.chat_ui_manager.chat_log

        for message in chat_log:
            messages.append({"role": message.role, "content": message.content})
        while messages[-1].get("role") == "assistant":
            messages.pop()
        logger.info(f"Messages: {messages}")

        response = await pydantic_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            response_model=response_model,
            messages=messages,
        )

        assert isinstance(response, ModelResponseToWeatherQuery)
        logger.info(f"GPT response: {response}")
        return response