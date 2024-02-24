from presentation.overview import load_interface
from presentation.ui_manager import ChatUIManager
from service.chat_service import ChatService
from service.weather_service import WeatherService
from service.user_service import UserService
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