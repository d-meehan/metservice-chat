from datetime import datetime
import asyncio
from nicegui import ui, Client, app
from loguru import logger
from ..schema import Message, GPTResponseToWeatherQuery
from ..service.chat import GPT_response
from ..service.weather_data import get_weather_data


@ui.page('/')
async def load_interface(client: Client):

    data_store = []
    chat_log: list[Message] = []


    async def get_user_location():
        if 'latitude' in app.storage.user and 'longitude' in app.storage.user:
            return
        response = await ui.run_javascript('''
            return await new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error('Geolocation is not supported by your browser'));
                } else {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            resolve({
                                latitude: position.coords.latitude,
                                longitude: position.coords.longitude,
                            });
                        },
                        () => {
                            reject(new Error('Unable to retrieve your location'));
                        }
                    );
                }
            });
        ''', timeout=10.0)
        logger.info(f"User location: {response}")
        app.storage.user['latitude'] = response['latitude']
        app.storage.user['longitude'] = response['longitude']

    @ui.refreshable
    def chat_messages():
        for message in chat_log:
            ui.chat_message(message.content, name=message.role, stamp=message.stamp, avatar=message.avatar, sent=message.sent)
        ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
        

    async def on_enter(e):
        # Append the user message to the messages list and refresh the UI
        user_message = e.value
        stamp = datetime.now().strftime("%H:%M")
        chat_log.append(Message(role="user", content=user_message, stamp=stamp, avatar="", sent=True))
        chat_messages.refresh()

        # Show spinner while processing
        with ui.spinner():
            nonlocal data_store
            # Get the response from the GPT model
            response = await GPT_response(user_message, chat_log, data_store, response_model=GPTResponseToWeatherQuery)

            # Process and append the response to messages, then update UI
            bot_stamp = datetime.now().strftime("%H:%M")
            chat_log.append(Message(role="assistant", content=response.response, stamp=bot_stamp, avatar="", sent=False))
            await client.connected()
            chat_messages.refresh()

            while response.weather_query_check and not response.sufficient_data_check:
                data_store = await get_weather_data(response, data_store)

                response = await GPT_response(user_message, chat_log, data_store, GPTResponseToWeatherQuery)
                bot_stamp = datetime.now().strftime("%H:%M")
                chat_log.append(Message(role="assistant", content=response.response, stamp=bot_stamp, avatar="", sent=False))
                chat_messages.refresh()

    
    anchor_style = r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
    ui.add_head_html(f'<style>{anchor_style}</style>')

    # the queries below are used to expand the content down to the footer (content can then use flex-grow to expand)
    ui.query('.q-page').classes('flex')
    ui.query('.nicegui-content').classes('w-full')

    with ui.tabs().classes('w-full') as tabs:
        chat_tab = ui.tab('Chat')
        logs_tab = ui.tab('Logs')
    with ui.tab_panels(tabs, value=chat_tab).classes(
        'w-full max-w-2xl mx-auto flex-grow items-stretch'
        ):
        with ui.tab_panel(chat_tab).classes('items-stretch'):
            chat_messages()
        with ui.tab_panel(logs_tab):
            log = ui.log().classes('w-full h-full')

    with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
        with ui.row().classes('w-full no-wrap items-center'):
            placeholder = 'message'
            text = ui.input(placeholder=placeholder).props('rounded outlined input-class=mx-3') \
                .classes('w-full self-center').on('keydown.enter', lambda e: on_enter(text))

        ui.markdown('simple chat app built with [NiceGUI](https://nicegui.io)') \
            .classes('text-xs self-end mr-8 m-[-1em] text-primary')
        
    await client.connected()
    await asyncio.sleep(1)
    await get_user_location()


# app.on_connect(get_user_location)
ui.run(title='WeatherBot', storage_secret='secret-key')