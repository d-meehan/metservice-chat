from collections.abc import Awaitable, Callable
import os
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger
from nicegui import ui

from models import Message, QueryClassification
from presentation.components import chart_options
from utils.constants import QueryTypesEnum, WeatherVarMap


class UIManager:
    """
    Class to manage and update the UI elements.
    """

    def __init__(self) -> None:
        self.chat_log: list[Message] = []
        self.map = None
        self.chart = None
        self.spinner = None
        self.send_button = None
        self.data_viz_column = None

    def load_ui(self) -> None:
        """Base UI layout."""
        anchor_style = r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
        ui.add_head_html(f'<style>{anchor_style}</style>')
        ui.query('.q-page').classes('flex')
        ui.query('.nicegui-content').classes('w-full')

    async def toggle_visual_processing(self, show_spinner: bool):
        """Toggles visibility of the UI elements based on the user interaction."""
        self.spinner.set_visibility(show_spinner)
        self.send_button.set_visibility(not show_spinner)

    def load_chat_column(self, callback: Callable[[ui.input], Awaitable]) -> None:
        """
        Loads chat column and checks for API keys in .env file, disabling messaging and displaying a message if they are not present.
        """
        load_dotenv()

        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', None)
        METSERVICE_API_KEY = os.environ.get('METSERVICE_API_KEY', None)
        with ui.column().classes('w-1/3 max-w-2xl items-stretch mx-auto h-full max-w-2xl px-4 h-full'):
            with ui.tab_panel(name='chat').classes('w-full h-5/6 px-4 border rounded-lg border-gray-300 max-w-2xl items-stretch overflow-auto flex-column-reverse overflow-anchor-auto'):
                # messages are reloaded on each new message
                self._display_messages()
            with ui.row().classes('w-full h-1/6 no-wrap bottom-5 mx-auto'):
                if OPENAI_API_KEY and METSERVICE_API_KEY:
                    placeholder = 'Message WeatherBot'
                    # input field is named component so elements can be added to it
                    text = ui.input(placeholder=placeholder).props('rounded outlined').classes(
                        'w-full self-center').on('keydown.enter', lambda e: callback(text))
                    with text:
                        self.send_button = ui.button(icon='send', on_click=lambda: callback(text)).props(
                            'round dense flat')
                        self.spinner = ui.spinner(
                            size='3em').classes('right-0 self-center')
                        self.spinner.set_visibility(False)
                else:
                    text = ui.input(placeholder='Please set API keys in .env file in project root.').props(
                        'rounded outlined').classes('w-full self-center')
                    with text:
                        self.send_button = ui.button('send').props(
                            'round dense flat').disable()
                        self.spinner = ui.spinner(size='3em').classes(
                            'right-0 self-center').set_visibility(False)
            ui.markdown('WeatherBot').classes(
                'absolute bottom-4 text-xs mr-7 text-primary')

    def load_data_visualization(self) -> None:
        """
        Loads data visualization column with map and chart. Data viz column is named so chart can be deleted and replaced on data change to work around NiceGUI/Highcharts issue.
        """
        with ui.column().classes('w-2/3 max-w-2/3 mx-auto items-stretch flex-grow px-4 h-full') as data_viz_column:
            m = ui.leaflet(center=(-36.85088270000001, 174.7644881),
                           zoom=10).classes('w-full h-2/3')
            m.clear_layers()
            m.tile_layer(
                url_template=r'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
                options={
                    'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                    'subdomains': 'abcd',
                    'maxZoom': 20
                }
            )
            self.map = m

            chart = ui.highchart(options=chart_options(), extras=[
                'windbarb', 'accessibility']).classes(
                'w-full h-full')
            self.chart = chart
        self.data_viz_column = data_viz_column

    async def add_message(self, role: str, content: str):
        """
        Loads message to chat log and refreshes chat display.
        """
        if role == "user":
            avatar = "https://www.gravatar.com/avatar/"
            sent = True
        else:
            avatar = "https://www.gravatar.com/avatar/"
            sent = False
        message = Message(
            role=role,
            content=content,
            stamp=datetime.now().strftime("%H:%M"),
            avatar=avatar,
            sent=sent
        )
        self.chat_log.append(message)
        self._display_messages.refresh()

    def update_map(self, lat_lng: tuple[float, float]) -> None:
        self.map.marker(latlng=(lat_lng))
        self.map.center = (lat_lng)

    def update_chart(self, weather_data: dict[str, list], classification: QueryClassification) -> None:
        """
        Updates the chart with weather data and classification information.
        """
        # delete and replace chart to work around Highcharts issue
        self.chart.delete()
        with self.data_viz_column:
            chart = ui.highchart(options=chart_options(), extras=[
                'windbarb', 'accessibility']).classes(
                'w-full h-full')
            self.chart = chart
        self.chart._props['options']['plotOptions']['series']['pointStart'] = weather_data['time_data'][0].timestamp(
        ) * 1000
        self.chart._props['options']['plotOptions']['series']['pointInterval'] = (
            weather_data['time_data'][1] - weather_data['time_data'][0]).seconds * 1000
        # general weather queries will showcase all weather data with icons, temperature acts as the base series
        if QueryTypesEnum.GENERAL_WEATHER in classification.query_type:
            self.chart._props['options']['series'][0]['data'] = [
                {'x': point['x'], 'y': point['y'],
                    'dataLabels': {
                        'enabled': True,
                        'useHTML': True,
                        'format': ('<div style="width: 30px; height: 30px; overflow: hidden; border-radius: 50%">' + f'<img src="{point["iconPath"]}"' + 'style="width: 30px"></div>')
                }} for point in weather_data.get(WeatherVarMap.temp, [])]
        else:
            # weather specific queries only loads queried weather type
            self.chart._props['options']['series'][0]['data'] = weather_data.get(
                WeatherVarMap.temp, [])
        self.chart._props['options']['series'][1]['data'] = weather_data.get(
            WeatherVarMap.rain, [])
        self.chart._props['options']['series'][2]['data'] = weather_data.get(
            WeatherVarMap.humidity, [])
        self.chart._props['options']['series'][3]['data'] = weather_data.get(
            WeatherVarMap.wind_speed, [])
        self.chart._props['options']['series'][4]['data'] = weather_data.get(
            WeatherVarMap.cloud_cover, [])
        self.chart._props['options']['title']['text'] = f"Weather Forecast for {
            classification.location.title()} on {classification.query_from_date.strftime('%A, %d %B %Y')}"
        self.chart.update()

    @ui.refreshable
    def _display_messages(self):
        for message in self.chat_log:
            ui.chat_message(message.content, name=message.role,
                            stamp=message.stamp, avatar=message.avatar, sent=message.sent)
        ui.run_javascript(
            "{const chatContainer = document.querySelector('.q-tab-panel.nicegui-tab-panel.overflow-auto'); if (chatContainer) {chatContainer.scrollTop = chatContainer.scrollHeight;}}")
