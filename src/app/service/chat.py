import os
from datetime import datetime
from pydantic import BaseModel
from loguru import logger
from nicegui import app
import instructor
import googlemaps
from dotenv import load_dotenv
import openai
from ..schema import GPTResponseToWeatherQuery, Message, MetserviceTimePointSummary
from ..utils.constants import METSERVICE_VARIABLES, SYSTEM_PROMPT

load_dotenv()

pydantic_client = instructor.apatch(openai.AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY']))
client = openai.AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])
gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

async def GPT_response(user_message: str, chat_log: list[Message], data_store: list[list[MetserviceTimePointSummary]], response_model: BaseModel) -> GPTResponseToWeatherQuery:
    """
    This function takes the user's message, the chat log, the data store, the response model and the app storage as input and returns the response from the GPT model.
    
    Parameters:
    user_message (str): The user's message
    chat_log (list[Message]): The chat log
    data_store (list[list[MetserviceTimePointSummary]]): The data store
    response_model (BaseModel): The response model
    app_storage (dict): The app storage
    """


    system_prompt = SYSTEM_PROMPT.format(
        current_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        latitude=app.storage.user['latitude'],
        longitude=app.storage.user['longitude'],
        data_store=data_store,
        vars=METSERVICE_VARIABLES
    )

    messages=[
            {
                "role": "system", 
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": user_message
            }
        ]
    
    while chat_log[-1].role == "assistant":
        chat_log.pop()
    for message in chat_log:
        print(message)
        messages.insert(-1, {"role": message.role, "content": message.content})
    logger.info(f"Messages: {messages}")

    response = await pydantic_client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_model=response_model,
        messages=messages,
    )

    assert isinstance(response, GPTResponseToWeatherQuery)
    logger.info(f"GPT response: {response}")
    return response