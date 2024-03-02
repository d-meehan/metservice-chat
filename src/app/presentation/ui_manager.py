from collections.abc import Awaitable, Callable
from datetime import datetime
from loguru import logger

from nicegui import ui
from models import Message, QueryClassification

from presentation.components import chart_options
from utils.constants import WeatherVarMap

class UIManager:
    def __init__(self) -> None:
        self.chat_log: list[Message] = []
        self.map = None
        self.chart = None
        self.spinner = None
        self.send_button = None

    def load_ui(self) -> None:
        anchor_style = r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
        ui.add_head_html(f'<style>{anchor_style}</style>')
        ui.query('.q-page').classes('flex')
        ui.query('.nicegui-content').classes('w-full')

    def toggle_visual_processing(self, show_spinner: bool):
        """Toggles visibility of the UI elements based on the user interaction."""
        self.spinner.set_visibility(show_spinner)
        self.send_button.set_visibility(not show_spinner)

    def load_chat_column(self, callback: Callable[[ui.input], Awaitable]) -> None:
        with ui.column().classes('w-1/3 max-w-2xl items-stretch mx-auto h-full max-w-2xl px-4 h-full'):
            with ui.tab_panel(name='chat').classes('w-full h-5/6 px-4 border rounded-lg border-gray-300 max-w-2xl items-stretch overflow-auto flex-column-reverse overflow-anchor-auto'):
                self._display_messages()
            with ui.row().classes('w-full h-1/6 no-wrap bottom-5 mx-auto'):
                placeholder = 'message'
                text = ui.input(placeholder=placeholder).props('rounded outlined').classes(
                    'w-full self-center').on('keydown.enter', lambda e: callback(text)).on(
                        'keydown.enter', lambda e: text.set_value(None))
                with text:
                    self.send_button = ui.button(icon='send').on('click', lambda e: callback(text)).props(
                        'round dense flat').on('click', lambda e: text.set_value(None))
                    self.spinner = ui.spinner(size='3em').classes('right-0 self-center')
                    self.spinner.set_visibility(False)
            ui.markdown('WeatherBot').classes(
                'absolute bottom-4 text-xs mr-7 text-primary')
            
    def load_data_visualization(self) -> None:
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
                self.map = m
                self.chart = ui.highchart(options=chart_options, extras=[
                                    'windbarb', 'accessibility']).classes(
                                        'w-full h-full')

    def add_message(self, role: str, content: str):
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
        logger.debug(f"weather_data: {weather_data}")
        self.chart.options['plotOptions']['series']['pointStart'] = weather_data['time_data'][0].timestamp() * 1000
        self.chart.options['plotOptions']['series']['pointInterval'] = (weather_data['time_data'][1] - weather_data['time_data'][0]).seconds * 1000
        self.chart.options['series'][0]['data'] = [
            {'x': point['x'], 'y': point['y'], 
                'dataLabels': {
                    'enabled': True, 
                    'useHTML': True, 
                    'format': ('<div style="width: 30px; height: 30px; overflow: hidden; border-radius: 50%">' + f'<img src="{point["iconPath"]}"' + 'style="width: 30px"></div>')
                }} for point in weather_data[WeatherVarMap.temp]]
        logger.info(f"chart.options['series'][0]['data']: {self.chart.options['series'][0]['data']}")
        self.chart.options['series'][1]['data'] = weather_data[WeatherVarMap.rain]
        self.chart.options['series'][2]['data'] = weather_data[WeatherVarMap.humidity]
        self.chart.options['series'][3]['data'] = weather_data[WeatherVarMap.wind_speed]
        self.chart.options['series'][4]['data'] = weather_data[WeatherVarMap.cloud_cover]
        self.chart.options['title']['text'] = f"Weather Forecast for {
            classification.location.title()} on {classification.query_from_date.strftime('%A, %d %B %Y')}"
        self.chart.update()

    @ui.refreshable
    def _display_messages(self):
        for message in self.chat_log:
            ui.chat_message(message.content, name=message.role,
                            stamp=message.stamp, avatar=message.avatar, sent=message.sent)
        ui.run_javascript(
            "{const chatContainer = document.querySelector('.q-tab-panel.nicegui-tab-panel.overflow-auto'); if (chatContainer) {chatContainer.scrollTop = chatContainer.scrollHeight;}}")
