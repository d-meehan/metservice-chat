
from nicegui import ui
from fastapi.responses import RedirectResponse
from components import test_options


@ui.page('/')
def home_page() -> RedirectResponse:
    return RedirectResponse('/chat')

@ui.page('/chat')
def test_page() -> None:
    def update_chart():
        chart.options['series'][0]['data'] = [1 for _ in range(24)]
        chart.update()
    chart = ui.highchart(options={
        'chart': {'marginBottom': 100, 'marginRight': 60, 'marginTop': 50, 'plotBorderWidth': 1,
                  'height': 400, 'alignTicks': False, 'scrollablePlotArea': {'minWidth': 650}},
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
            },
        ],
    }, extras=['windbarb', 'accessibility'])
    # chart = ui.highchart(options=test_options, extras=['windbarb', 'accessibility'])
    ui.button('Update chart', on_click=lambda e: update_chart())
ui.run()