from src.app.presentation.overview import load_interface
from src.app.presentation.ui_manager import ChatUIManager
from src.app.service.chat_service import ChatService
from src.app.service.weather_service import WeatherService
from src.app.service.user_service import UserService
from nicegui import ui
from loguru import logger

def main():
    logger.info("Starting WeatherBot")
    user_service = UserService()
    weather_service = WeatherService(user_service)
    chat_ui_manager = ChatUIManager()
    chat_service = ChatService(weather_service, chat_ui_manager)
    load_interface(chat_service)
    ui.run(title="WeatherBot", storage_secret="secret-key")


if __name__ in {"__main__", "__mp_main__"}:
    main()