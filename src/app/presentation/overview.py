from datetime import datetime
from nicegui import ui, Client
from loguru import logger
from service.chat_service import ChatService
from models import QueryClassification, Message
from presentation.components import chart_options, gen_query_series_to_chart, fetch_weather_icons


def load_interface(chat_service: ChatService) -> None:
    
    @ui.page('/')
    async def chat_page():
        async def handle_message(e):
            nonlocal chart
            chat_service.chat_ui_manager.add_message_to_log(
                    role="user",
                    content=e.value,
                    )
            send_button.set_visibility(False)
            spinner.set_visibility(True)
            # chat_window.scroll_to(percent=1)
            classification: QueryClassification = await chat_service.process_message()
            # chat_window.scroll_to(percent=1)
            spinner.set_visibility(False)
            send_button.set_visibility(True)
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
            chart = gen_query_series_to_chart(chart, time_data, temp_icon_data, precip_data, humidity_data, wind_data, cloud_data)
            chart.options['title']['text'] = f"Weather Forecast for {classification.location.title()} on {classification.query_from_date.strftime('%A, %d %B %Y')}"
            chart.update()


        anchor_style = r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
        ui.add_head_html(f'<style>{anchor_style}</style>')

        # # the queries below are used to expand the content down to the footer (content can then use flex-grow to expand)
        ui.query('.q-page').classes('flex')
        ui.query('.nicegui-content').classes('w-full')

        with ui.row().classes('h-full w-full no-wrap items-stretch max-h-screen'):
            with ui.column().classes('w-1/3 max-w-2xl items-stretch mx-auto h-full max-w-2xl px-4 h-full'):
                with ui.tab_panel(name='chat').classes('w-full h-5/6 px-4 border rounded-lg border-gray-300 max-w-2xl items-stretch overflow-auto flex-column-reverse overflow-anchor-auto'):
                    chat_service.chat_ui_manager.display_messages()
                with ui.row().classes('w-full h-1/6 no-wrap bottom-5 mx-auto'):
                    placeholder = 'message'
                    text = ui.input(placeholder=placeholder).props('rounded outlined') \
                        .classes('w-full self-center').on('keydown.enter', lambda e: handle_message(text)).on('keydown.enter', lambda e: text.set_value(None))
                    with text:
                        send_button = ui.button(icon='send').on('click', lambda e: handle_message(text)).props('round dense flat').on('click', lambda e: text.set_value(None))
                        spinner = ui.spinner(size='3em').classes('right-0 self-center')
                        spinner.set_visibility(False)
                ui.markdown('WeatherBot').classes('absolute bottom-4 text-xs mr-7 text-primary')
            with ui.column().classes('w-2/3 max-w-2/3 mx-auto items-stretch flex-grow px-4 h-full'):
                m = ui.leaflet(center=(-36.85088270000001, 174.7644881), zoom=10).classes('w-full h-2/3')
                m.clear_layers()
                m.tile_layer(
                    url_template=r'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
                    options={
                        'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                        'subdomains': 'abcd',
                        'maxZoom': 20
                    }
                )
                chart = ui.highchart(options=chart_options, extras=[
                                    'windbarb', 'accessibility']).classes('w-full h-full')
