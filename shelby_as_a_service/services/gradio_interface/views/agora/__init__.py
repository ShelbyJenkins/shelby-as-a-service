from typing import Literal

from services.gradio_interface.views.agora.edit_tab import EditTab
from services.gradio_interface.views.agora.generate_tab import GenerateTab
from services.gradio_interface.views.agora.search_tab import SearchTab

AVAILABLE_CLASSES_TYPINGS = Literal[
    GenerateTab.class_name,
    SearchTab.class_name,
    EditTab.class_name,
]
AVAILABLE_CLASSES_NAMES: list[str] = [
    GenerateTab.CLASS_NAME,
    SearchTab.CLASS_NAME,
    EditTab.CLASS_NAME,
]
AVAILABLE_CLASSES_UI_NAMES = [
    GenerateTab.CLASS_UI_NAME,
    SearchTab.CLASS_UI_NAME,
    EditTab.CLASS_UI_NAME,
]
AVAILABLE_CLASSES = [
    GenerateTab,
    SearchTab,
    EditTab,
]
