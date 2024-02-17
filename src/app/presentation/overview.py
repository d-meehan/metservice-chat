from nicegui import ui, Client
from loguru import logger
from ..service.chat_service import ChatService



def load_interface(chat_service: ChatService) -> None:
    @ui.page('/')
    async def chat_page():
        async def handle_message(e):
            with ui.spinner():
                response = await chat_service.process_message(e.value)
        
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
                chat_service.chat_ui_manager.display_messages()
            with ui.tab_panel(logs_tab):
                log = ui.log().classes('w-full h-full')

        with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
            with ui.row().classes('w-full no-wrap items-center'):
                placeholder = 'message'
                text = ui.input(placeholder=placeholder).props('rounded outlined input-class=mx-3') \
                    .classes('w-full self-center').on('keydown.enter', lambda e: handle_message(text))

            ui.markdown('simple chat app built with [NiceGUI](https://nicegui.io)') \
                .classes('text-xs self-end mr-8 m-[-1em] text-primary')