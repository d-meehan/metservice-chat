import os
from typing import Optional
from fastapi.responses import RedirectResponse
from nicegui import ui, app
from loguru import logger

from service.chat_service import ChatService
from models import QueryClassification
from utils.constants import QueryTypesEnum
from utils.auth import AuthMiddleware


@ui.page('/')
def load_interface(chat_service: ChatService) -> None:
    app.add_middleware(AuthMiddleware)

    @ui.page('/login')
    def login_page() -> Optional[RedirectResponse]:
        def try_login() -> None:  # local function to avoid passing username and password as arguments
            logger.info(f"{app.storage.user.get('referrer_path', '/')}")
            if password.value == os.environ.get('PASSWORD'):
                app.storage.user.update({'authenticated': True})
                logger.info(f"User authenticated: {app.storage.user.get('authenticated', False)}")
                # go back to where the user wanted to go
                ui.navigate.to(app.storage.user.get('referrer_path', '/'))
            else:
                ui.notify('Wrong password', color='negative')

        if app.storage.user.get('authenticated', False):
            logger.info(f"User authenticated: {app.storage.user.get('authenticated', False)}, redirecting to /chat")
            return RedirectResponse('/chat')
        with ui.card().classes('absolute-center'):
            password = ui.input('Password', password=True, password_toggle_button=True).on(
                'keydown.enter', try_login)
            ui.button('Log in', on_click=try_login)
        return None
    
    @ui.page('/chat')
    async def chat_page() -> None:
        logger.info(f"loading chat page for user: {app.storage.user}")
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
                weather_data = await chat_service.weather_service.fetch_weather_icons(weather_data)
            chat_service.ui_manager.update_chart(weather_data, classification)

        chat_service.ui_manager.load_ui()
        with ui.row().classes('h-full w-full no-wrap items-stretch max-h-screen'):
            chat_service.ui_manager.load_chat_column(callback=chat_callback)
            chat_service.ui_manager.load_data_visualization()