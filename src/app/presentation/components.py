from nicegui import ui, events, app

user_message = ui.chat_message('Hello, world!', name='User', sent=True, avatar='https://cdn.quasar.dev/img')

# general
with ui.section(): # with creates parent relationship
    ui.label('Hello, world!') # label
row = ui.row() # row

with row:
    ui.label('Hello, world!') # adds label to existing row

row.remove # removes element from row
row.clear # removes all elements from row

ui.scroll_area # creates scrollable components
ui.separator # separator line
ui.splitter # resizable sections

with ui.row().classes('w-full border'):
    ui.label('Left')
    ui.space() # fills space between elements
    ui.label('Right')

ui.tooltip # expanding tooltip for buttons
ui.notify # notification for user

# notification that updates
async def compute():
    n = ui.notification(timeout=None)
    for i in range(10):
        n.message = f'Computing {i/10:.0%}'
        n.spinner = True
        await asyncio.sleep(0.2)
    n.message = 'Done!'
    n.spinner = False
    await asyncio.sleep(1)
    n.dismiss()

ui.button('Compute', on_click=compute)

# menu with button
with ui.row().classes('w-full items-center'):
    result = ui.label().classes('mr-auto')
    with ui.button(icon='menu'):
        with ui.menu() as menu:
            ui.menu_item('Menu item 1', lambda: result.set_text('Selected item 1'))
            ui.menu_item('Menu item 2', lambda: result.set_text('Selected item 2'))
            ui.menu_item('Menu item 3 (keep open)',
                         lambda: result.set_text('Selected item 3'), auto_close=False)
            ui.separator()
            ui.menu_item('Close', on_click=menu.close)

ui.query('body').style = 'background-color: #f0f0f0' # change aspect of specified element
ui.timer # ongoing timer that can call a function at a specified interval or after a specified time, can be cancelled or set active by other elements

@ui.refreshable # decorates a function so when it's call all of the elements it generates are deleted and replaced
def refreshable():
    return ui.label('Hello, world!')

ui.button("test").on('mousedown', lambda: ui.refreshable()) # custom event handling
app.storage.user # storage for user data persistence

# open url in new tab
url = 'https://github.com/zauberzeug/nicegui/'
ui.button('Open GitHub', on_click=lambda: ui.open(url, new_tab=True))


# async pattern
async def async_task():
    ui.notify('Asynchronous task started')
    await asyncio.sleep(5)
    ui.notify('Asynchronous task finished')

# track keyboard input
def handle_key(e: KeyEventArguments):
    if e.key == 'f' and not e.action.repeat:
        if e.action.keyup:
            ui.notify('f was just released')
        elif e.action.keydown:
            ui.notify('f was just pressed')
    if e.modifiers.shift and e.action.keydown:
        if e.key.arrow_left:
            ui.notify('going left')
        elif e.key.arrow_right:
            ui.notify('going right')
        elif e.key.arrow_up:
            ui.notify('going up')
        elif e.key.arrow_down:
            ui.notify('going down')

keyboard = ui.keyboard(on_key=handle_key)

# chat interface
ui.button # button
ui.input # text input
ui.avatar # avatar for user and model
ui.image  # image for showcasing weather results
with ui.image():
    ui.label('Hello, world!') # overlay on images
ui.spinner # spinner for loading

# weather interface
ui.table # table for weather results
ui.icon  # icon for weather results
ui.highchart # highchart for weather results
ui.leaflet # map for weather results
ui.carousel # interactive carousel of images 

#making images handle mouse interactions
def mouse_handler(e: events.MouseEventArguments):
    color = 'SkyBlue' if e.type == 'mousedown' else 'SteelBlue'
    ii.content += f'<circle cx="{e.image_x}" cy="{
        e.image_y}" r="15" fill="none" stroke="{color}" stroke-width="4" />'
    ui.notify(f'{e.type} at ({e.image_x:.1f}, {e.image_y:.1f})')

src = 'https://picsum.photos/id/565/640/360'
ii = ui.interactive_image(src, on_mouse=mouse_handler, events=[
                          'mousedown', 'mouseup'], cross=True)

# svg image
content = '''
    <svg viewBox="0 0 200 200" width="100" height="100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="78" fill="#ffde34" stroke="black" stroke-width="3" />
    <circle cx="80" cy="85" r="8" />
    <circle cx="120" cy="85" r="8" />
    <path d="m60,120 C75,150 125,150 140,120" style="fill:none; stroke:black; stroke-width:8; stroke-linecap:round" />
    </svg>'''
ui.html(content)







