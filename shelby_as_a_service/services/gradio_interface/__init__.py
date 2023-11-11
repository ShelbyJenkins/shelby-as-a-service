from typing import Literal

from services.gradio_interface.views.context_index_view import DocIndexView
from services.gradio_interface.views.main_chat_view import MainChatView
from services.gradio_interface.views.settings_view import SettingsView

AVAILABLE_VIEW_NAMES = Literal[
    DocIndexView.class_name,
    MainChatView.class_name,
    SettingsView.class_name,
]
AVAILABLE_VIEWS = [
    DocIndexView,
    MainChatView,
    SettingsView,
]
