from typing import Literal

from services.gradio_interface.views.advanced.advanced_view import AdvancedView
from services.gradio_interface.views.agora.agora_view import AgoraView
from services.gradio_interface.views.extensions_view import ExtensionsView

AVAILABLE_CLASSES_TYPINGS = Literal[
    AgoraView.class_name,
    AdvancedView.class_name,
    ExtensionsView.class_name,
]
AVAILABLE_CLASSES_NAMES: list[str] = [
    AgoraView.CLASS_NAME,
    AdvancedView.CLASS_NAME,
    ExtensionsView.CLASS_NAME,
]
AVAILABLE_CLASSES_UI_NAMES = [
    AgoraView.CLASS_UI_NAME,
    AdvancedView.CLASS_UI_NAME,
    ExtensionsView.CLASS_UI_NAME,
]
AVAILABLE_CLASSES = [
    AgoraView,
    AdvancedView,
    ExtensionsView,
]
