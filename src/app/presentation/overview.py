from collections.abc import Awaitable
from datetime import datetime
from nicegui import ui, Client
from loguru import logger
from service.chat_service import ChatService
from models import QueryClassification, Message
from presentation.components import chart_options, configure_page_layout, gen_query_series_to_chart, fetch_weather_icons


# def load_interface(chat_service: ChatService) -> None:
#     ui.page('/')

#     async def chat_page():
#         setup_page_layout()
#         send_button, spinner, text_input = init_message_input_area(process_message)
#         chart, map_view = init_chat_ui()

#         async def process_message(e):
#             nonlocal chart
#             user_message = e.value
#             await process_user_message(chat_service, user_message, send_button, spinner, chart, map_view)

#     ui.run(title="WeatherBot", storage_secret="secret-key")


# def setup_page_layout():
#     """Sets up the overall page layout and styles."""
#     anchor_style = 'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
#     ui.add_head_html(f'<style>{anchor_style}</style>')
#     ui.query('.q-page').classes('flex')
#     ui.query('.nicegui-content').classes('w-full')


# def init_message_input_area(process_message):
#     """Initializes the message input area and returns the send button, spinner, and text input elements."""
#     with ui.row().classes('w-full h-1/6 no-wrap bottom-5 mx-auto'):
#         text_input = ui.input(placeholder='Type your message here...').classes(
#             'w-full self-center')
#         send_button = ui.button(icon='send').classes(
#             'ml-2').on('click', lambda e: process_message(text_input))
#         spinner = ui.spinner(size='3em').classes('hidden')
#     return send_button, spinner, text_input


# async def process_user_message(chat_service: ChatService, user_message: str, send_button, spinner, chart, map_view):
#     """Processes the user message, updates the UI, and handles any required service interactions."""
#     toggle_ui_elements(send_button, spinner, show_spinner=True)
#     classification = await chat_service.process_message(user_message)
#     if classification.query_type != ["non-weather"]:
#         await update_map_and_chart(chat_service, classification, chart, map_view)
#     toggle_ui_elements(send_button, spinner, show_spinner=False)






def load_interface(chat_service: ChatService) -> None:
    @ui.page('/')
    async def chat_page():
        async def process_message(e: ui.input):
            classification: QueryClassification = await chat_service.classify_query()
            if classification.query_type != ["non-weather"]:
                await chat_service.weather_service.get_weather_data(classification)
            chat_service.ui_manager.toggle_visual_processing(show_spinner=False)
            logger.info(f"Classification: {classification}")
            if classification.query_type == ["non-weather"]:
                return
            lat_lng = await chat_service.weather_service._location_to_lat_lon(classification.location)
            logger.info(f"lat_lng: {lat_lng}")
            
            m.marker(latlng=lat_lng)
            m.set_center(lat_lng)
            
            
            
            logger.info(f"Map shown for location: {classification.location}")
            # find data store that matches classification
            temp_data = []
            precip_data = []
            humidity_data = []
            wind_data = []
            cloud_data = []
            time_data = []
            for data in chat_service.weather_service.data_store:
                if data.weather_data_type == classification.query_type and data.location == classification.location and data.date == classification.query_from_date:
                    logger.info(f"Data found for location: {classification.location}, date: {classification.query_from_date} and type: {classification.query_type}")
                    for hour_summary in data.hour_summaries:
                        time_data.append(datetime.combine(data.date, hour_summary.hour))
                        for variable in hour_summary.variables:
                            if variable.name == 'air.temperature.at-2m':
                                temp_data.append(variable.value)
                            elif variable.name == 'precipitation.rate':
                                precip_data.append(variable.value)
                            elif variable.name == 'air.humidity.at-2m':
                                humidity_data.append(variable.value)
                            elif variable.name == 'wind.speed.at-10m':
                                wind_speed = variable.value
                            elif variable.name == 'wind.direction.at-10m':
                                wind_direction = variable.value
                            elif variable.name == 'cloud.cover':
                                cloud_data.append(variable.value)
                        if wind_speed and wind_direction:
                            wind_hour_data = [wind_speed, wind_direction]
                        wind_data.append(wind_hour_data)
            temp_icon_data = fetch_weather_icons(time_data=time_data, rain_data=precip_data, wind_data=wind_data, cloud_data=cloud_data, temp_data=temp_data)
            chart.options['series'][0]['data'] = time_data
            chart = gen_query_series_to_chart(chart, time_data, temp_icon_data, precip_data, humidity_data, wind_data, cloud_data)
            chart.options['title']['text'] = f"Weather Forecast for {classification.location.title()} on {classification.query_from_date.strftime('%A, %d %B %Y')}"
            chart.update()
        configure_page_layout()
        with ui.row().classes('h-full w-full no-wrap items-stretch max-h-screen'):
            chat_service.ui_manager.load_chat_column(callback=process_message)
            chat_service.ui_manager.load_data_visualization()





