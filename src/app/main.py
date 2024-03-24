import os

from nicegui import ui
from loguru import logger

from presentation.overview import load_interface

def main():
    port = int(os.environ.get('PORT', 80))
    logger.info("Starting WeatherBot")
    load_interface()
    ui.run(title="WeatherBot", storage_secret="secret-key", port=port, host="0.0.0.0")


if __name__ in {"__main__", "__mp_main__"}:
    main()