from nicegui import ui
from loguru import logger

from service.chat_service import ChatService
from models import QueryClassification
from utils.constants import QueryTypesEnum

def load_interface(chat_service: ChatService) -> None:
    @ui.page('/')
    async def chat_page() -> None:
        async def chat_callback(e: ui.input) -> None:
            classification: QueryClassification = await chat_service.classify_query(query=e.value)
            if QueryTypesEnum.NON_WEATHER in classification.query_type:
                logger.info("Query type is not weather related")
                await chat_service.process_message()
                return
            logger.info("Query type is weather related")
            metservice_response = await chat_service.weather_service.get_weather_data(classification)
            await chat_service.process_message()

            latitude = metservice_response[0].latitude
            longitude = metservice_response[0].longitude
            chat_service.ui_manager.update_map((latitude, longitude))
            logger.info(f"Map shown for location: {classification.location}")

            weather_data = await chat_service.weather_service.fetch_data(classification)
            if QueryTypesEnum.GENERAL_WEATHER in classification.query_type:
                logger.info(f"Query types: {classification.query_type} includes: {QueryTypesEnum.GENERAL_WEATHER}")
                weather_data = await chat_service.weather_service.fetch_weather_icons(weather_data)
            chat_service.ui_manager.update_chart(weather_data, classification)

        chat_service.ui_manager.load_ui()
        with ui.row().classes('h-full w-full no-wrap items-stretch max-h-screen'):
            chat_service.ui_manager.load_chat_column(callback=chat_callback)
            chat_service.ui_manager.load_data_visualization()





