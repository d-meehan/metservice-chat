from datetime import datetime
from loguru import logger
from nicegui import ui
from utils.constants import WeatherIconMap

def configure_page_layout() -> None:
        anchor_style = r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
        ui.add_head_html(f'<style>{anchor_style}</style>')

        # # the queries below are used to expand the content down to the footer (content can then use flex-grow to expand)
        ui.query('.q-page').classes('flex')
        ui.query('.nicegui-content').classes('w-full')

# Basic Highchart configuration for weather visualization
chart_options = {
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
}


def gen_query_series_to_chart(chart: ui.highchart, time_data: list[datetime], temp_data: list, precip_data: list, humidity_data: list, wind_data: list[list], cloud_data: list) -> ui.highchart:
    """
    This function takes the chart and the data as input and returns the chart with the data added to it.

    Parameters:
    chart (ui.highchart): The chart
    time_data (list): The time data
    temp_data (list): The temperature data
    precip_data (list): The precipitation data
    humidity_data (list): The humidity data
    wind_data (list[list]): The wind data
    cloud_data (list): The cloud data
    """
    chart.options['plotOptions']['series']['pointStart'] = time_data[0].timestamp() * 1000
    chart.options['plotOptions']['series']['pointInterval'] = (time_data[1] - time_data[0]).seconds * 1000
    chart.options['series'][0]['data'] = [
        {'x': point['x'], 'y': point['y'], 
            'dataLabels': {
                'enabled': True, 
                'useHTML': True, 
                'format': ('<div style="width: 30px; height: 30px; overflow: hidden; border-radius: 50%">' + f'<img src="{point["iconPath"]}"' + 'style="width: 30px"></div>')
            }} for point in temp_data]
    logger.info(f"chart.options['series'][0]['data']: {chart.options['series'][0]['data']}")
    chart.options['series'][1]['data'] = precip_data
    chart.options['series'][2]['data'] = humidity_data
    chart.options['series'][3]['data'] = wind_data
    chart.options['series'][4]['data'] = cloud_data

    return chart


def categorize_weather(prec_mm: float, wind_km_h: float, cloud_pct: float, temp_c: float) -> str:
    try:
        if temp_c < 0 and 0 <= prec_mm <= 0.2 and wind_km_h < 40:
            return 'frost'
        elif 0 <= prec_mm <= 0.2 and wind_km_h < 40:
            if cloud_pct < 10:
                return 'fine'
            elif cloud_pct <= 70:
                return 'partly_cloudy'
            else:
                return 'cloudy'
        elif 0.2 < prec_mm < 2 and wind_km_h < 40:
            return 'few_showers'
        elif 2 <= prec_mm <= 6 and wind_km_h < 40:
            return 'showers'
        elif prec_mm > 6 and wind_km_h < 40:
            return 'rain'
        elif wind_km_h >= 40:
            return 'wind'
        else:
            return 'Unspecified'
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 'Error'


def fetch_weather_icons(time_data: list[datetime], rain_data: list[float], wind_data: list[float], cloud_data: list[float], temp_data: list[float]) -> list[dict]:
    """
    This function takes the data as input and returns the weather icons.

    Parameters:
    rain_data (list): The rain data
    wind_data (list): The wind data
    cloud_data (list): The cloud data
    temp_data (list): The temperature data
    """
    weather_classification = []
    temp_icon_data = []
    for time, prec_mm, wind, cloud_pct, temp_c in zip(time_data, rain_data, wind_data, cloud_data, temp_data):
        weather_classification.append(categorize_weather(prec_mm, wind[0], cloud_pct, temp_c))
        temp_dict = {'x': time.timestamp() * 1000, 'y': temp_c, 'iconPath': ''}
        temp_icon_data.append(temp_dict)
    for idx, classification in enumerate(weather_classification):
        logger.info(f"time: {time_data[idx].time()} Classification: {classification}")
        if datetime.strptime('00:00:00', '%H:%M:%S').time() <= time_data[idx].time() < datetime.strptime('06:00:00', '%H:%M:%S').time() or datetime.strptime('18:00:00', '%H:%M:%S').time() < time_data[idx].time() <= datetime.strptime('23:00:00', '%H:%M:%S').time():
            classification += '_night'
        else:
            classification += '_day'
        weather_icon = WeatherIconMap[classification].value
        temp_icon_data[idx]['iconPath'] = weather_icon
    return temp_icon_data

                
            

