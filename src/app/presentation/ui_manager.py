from collections.abc import Awaitable, Callable
import os
from datetime import datetime

from dotenv import load_dotenv
from nicegui import ui

from models import Message, QueryClassification
from utils.constants import QueryTypesEnum, WeatherVarMap


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

    async def toggle_visual_processing(self, show_spinner: bool):
        """Toggles visibility of the UI elements based on the user interaction."""
        self.spinner.set_visibility(show_spinner)
        self.send_button.set_visibility(not show_spinner)

    def load_chat_column(self, callback: Callable[[ui.input], Awaitable]) -> None:
        load_dotenv()

        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', None)
        METSERVICE_API_KEY = os.environ.get('METSERVICE_API_KEY', None)
        with ui.column().classes('w-1/3 max-w-2xl items-stretch mx-auto h-full max-w-2xl px-4 h-full'):
            with ui.tab_panel(name='chat').classes('w-full h-5/6 px-4 border rounded-lg border-gray-300 max-w-2xl items-stretch overflow-auto flex-column-reverse overflow-anchor-auto'):
                self._display_messages()
            with ui.row().classes('w-full h-1/6 no-wrap bottom-5 mx-auto'):
                if OPENAI_API_KEY and METSERVICE_API_KEY:
                    placeholder = 'Message WeatherBot'
                    text = ui.input(placeholder=placeholder).props('rounded outlined').classes(
                        'w-full self-center').on('keydown.enter', lambda e: callback(text)).on(
                        'keydown.enter', lambda e: text.set_value(None))
                    with text:
                        self.send_button = ui.button(icon='send').on('click', lambda e: callback(text)).props(
                            'round dense flat').on('click', lambda e: text.set_value(None))
                        self.spinner = ui.spinner(size='3em').classes('right-0 self-center')
                        self.spinner.set_visibility(False)
                else:
                    text = ui.input(placeholder='Please set API keys in .env file in project root.').props(
                        'rounded outlined').classes('w-full self-center')
                    with text:
                        self.send_button = ui.button('send').props('round dense flat').disable()
                        self.spinner = ui.spinner(size='3em').classes('right-0 self-center').set_visibility(False)
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

                # temporary mess pending better solution to persistent chart
                chart = ui.highchart(options= {
    'time': {'useUTC': False},
    'title': {'text': 'Weather Forecast', 'align': 'left',
            'style': {
                'whiteSpace': 'nowrap',
                'textOverflow': 'ellipsis'},
            },
    'chart': {'marginBottom': 100, 'marginRight': 60, 'marginTop': 50, 'plotBorderWidth': 1,
            'height': 400, 'alignTicks': False, 'scrollablePlotArea': {'minWidth': 650}},
    'credits': {'text': 'Forecast from <a href="https://metservice.com">Metservice</a>',
                'href': 'https://metservice.com',
                'position': {'x': -40}
            },
    'xAxis': {
        'type': 'datetime',
        'title': {'text': 'Time'},
        'tickInterval': 36e5,  # Two hours
        'minorTickInterval': 36e5,  # One hour
        'tickLength': 0,
        'gridLineWidth': 1,
        'gridLineColor': 'rgba(128, 128, 128, 0.1)',
        'startOnTick': False,
        'endOnTick': False,
        'minPadding': 0,
        'maxPadding': 0,
        'offset': 30,
        'showLastLabel': True,
        'labels': {'format': '{value:%H}'},
        'crosshair': True
    },
    'yAxis': [{  # Primary yAxis for temperature
        'title': False,
        'labels': {
            'format': '{value}°',
            'style': {
                'fontSize': '10px'
            },
            'x': -3
        },
        'plotLines': [{  # Zero plane
            'value': 0,
            'color': '#BBBBBB',
            'width': 1,
            'zIndex': 2
        }],
        'maxPadding': 0.03,
        'minRange': 8,
        'tickInterval': 1,
        'gridLineColor': 'rgba(128, 128, 128, 0.1)'
    }, {  # Secondary yAxis for precipitation
        'title': None,
        'labels': {'enabled': False},
        'gridLineWidth': 0,
        'tickLength': 0,
        'minRange': 10,
        'min': 0
    }, {  # Tertiary yAxis for humidity
        'allowDecimals': False,
        'title': {'text': 'Humidity %', 'offset': 0, 'align': 'high', 'rotation': 0,
                'style': {'fontSize': '10px', 'color': '#7cb5ec'},
                'textAlign': 'left', 'x': 3},
        'labels': {'style': {'fontSize': '8px', 'color': '#7cb5ec'}, 'y': 2, 'x': 3},
        'gridLineWidth': 0,
        'opposite': True,
        'showLastLabel': False
    }],
    'tooltip': {
        'shared': True,
        'useHTML': True,
        'headerFormat': '<small>{point.x:%A, %b %e, %H:%M} - {point.point.to:%H:%M}</small><br>' +
        '<b>{point.point.symbolName}</b><br>'
    },
    'legend': {'enabled': False},
    'plotOptions': {'series': {'pointPlacement': 'between'},
    },
    'series': [
        {
            'name': 'Temperature',
            'data': [],  # To be filled with data
            'type': 'spline',
            'marker': {'enabled': False, 'states': {'hover': {'enabled': True}}},
            'tooltip': {'pointFormat': '<span style="color:{point.color}">\u25CF</span> ' +
                        '{series.name}: <b>{point.y}°C</b><br/>'},
            'zIndex': 1,
            'color': '#FF3333',
            'negativeColor': '#48AFE8'
        }, {
            'name': 'Precipitation',
            'data': [],  # To be filled with data
            'type': 'column',
            'color': '#68CFE8',
            'yAxis': 1,
            'groupPadding': 0,
            'pointPadding': 0,
            'grouping': False,
            'dataLabels': {
                    'enabled': True,
                    'filter': {'operator': '>', 'property': 'y', 'value': 0},
                    'style': {'fontSize': '8px', 'color': '#666'}
            },
            'tooltip': {'valueSuffix': ' mm'}
        }, {
            'name': 'Humidity',
            'color': '#7cb5ec',
            'data': [],  # To be filled with data
            'marker': {'enabled': False},
            'shadow': False,
            'tooltip': {'valueSuffix': ' %'},
            'dashStyle': 'shortdot',
            'yAxis': 2
        }, {
            'name': 'Wind',
            'type': 'windbarb',
            'id': 'windbarbs',
            'color': '#434348',
            'lineWidth': 1.5,
            'data': [],  # To be filled with data
            'vectorLength': 18,
            'yOffset': -15,
            'tooltip': {'valueSuffix': ' km/h'}
        }, {
            'name': 'Cloud cover',
            'data': [],  # To be filled with data
            'type': 'area',
            'color': '#7cb5ec',
            'fillOpacity': 0.3,
            'tooltip': {'valueSuffix': ' %'},
            'visible': False
        }
    ],
}, extras=[
                                    'windbarb', 'accessibility']).classes(
                                        'w-full h-full')
                self.chart = chart

    async def add_message(self, role: str, content: str):
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
        self.chart.options['plotOptions']['series']['pointStart'] = weather_data['time_data'][0].timestamp() * 1000
        self.chart.options['plotOptions']['series']['pointInterval'] = (weather_data['time_data'][1] - weather_data['time_data'][0]).seconds * 1000
        if QueryTypesEnum.GENERAL_WEATHER in classification.query_type:
            self.chart.options['series'][0]['data'] = [
                {'x': point['x'], 'y': point['y'], 
                    'dataLabels': {
                        'enabled': True, 
                        'useHTML': True, 
                        'format': ('<div style="width: 30px; height: 30px; overflow: hidden; border-radius: 50%">' + f'<img src="{point["iconPath"]}"' + 'style="width: 30px"></div>')
                    }} for point in weather_data.get(WeatherVarMap.temp, [])]
        else:
            self.chart.options['series'][0]['data'] = weather_data.get(WeatherVarMap.temp, [])
        self.chart.options['series'][1]['data'] = weather_data.get(WeatherVarMap.rain, [])
        self.chart.options['series'][2]['data'] = weather_data.get(WeatherVarMap.humidity, [])
        self.chart.options['series'][3]['data'] = weather_data.get(WeatherVarMap.wind_speed, [])
        self.chart.options['series'][4]['data'] = weather_data.get(WeatherVarMap.cloud_cover, [])
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
