import os

from nicegui import ui
from loguru import logger

from presentation.overview import load_interface
from presentation.ui_manager import UIManager
from service.chat_service import ChatService
from service.weather_service import WeatherService
from service.user_service import UserService

def main():
    port = int(os.environ.get('PORT', 80))
    logger.info("Starting WeatherBot")
    user_service = UserService()
    weather_service = WeatherService()
    ui_manager = UIManager()
    chat_service = ChatService(weather_service=weather_service, ui_manager=ui_manager, user_service=user_service)
    load_interface(chat_service)
    ui.run(title="WeatherBot", storage_secret="secret-key", port=port, host="0.0.0.0")


if __name__ in {"__main__", "__mp_main__"}:
    main()