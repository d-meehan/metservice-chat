


def chart_options() -> dict:
    return {
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