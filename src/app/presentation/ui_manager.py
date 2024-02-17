from nicegui import ui
from ..models import Message

class ChatUIManager:
    def __init__(self) -> None:
        self.chat_log: list[Message] = []

    def add_message_to_log(self, message: Message):
        self.chat_log.append(message)
        self.display_messages.refresh()

    @ui.refreshable
    def display_messages(self):
        for message in self.chat_log:
            ui.chat_message(message.content, name=message.role, stamp=message.stamp, avatar=message.avatar, sent=message.sent)
        ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)')
