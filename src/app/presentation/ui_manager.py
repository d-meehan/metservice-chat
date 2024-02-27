from datetime import datetime
from nicegui import ui
from models import Message

class ChatUIManager:
    def __init__(self) -> None:
        self.chat_log: list[Message] = []

    def add_message_to_log(self, role: str, content: str):
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
        self.display_messages.refresh()

    @ui.refreshable
    def display_messages(self):
        for message in self.chat_log:
            ui.chat_message(message.content, name=message.role, stamp=message.stamp, avatar=message.avatar, sent=message.sent)
        ui.run_javascript("{const chatContainer = document.querySelector('.q-tab-panel.nicegui-tab-panel.overflow-auto'); if (chatContainer) {chatContainer.scrollTop = chatContainer.scrollHeight;}}")
