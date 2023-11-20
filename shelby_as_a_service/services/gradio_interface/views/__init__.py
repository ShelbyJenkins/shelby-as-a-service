from typing import Literal

from services.gradio_interface.views.advanced_view import AdvancedView
from services.gradio_interface.views.doc_index_view import DocIndexView
from services.gradio_interface.views.generate_view import GenerateView
from services.gradio_interface.views.search_view import SearchView

AVAILABLE_VIEWS_TYPINGS = Literal[
    GenerateView.class_name,
    SearchView.class_name,
    DocIndexView.class_name,
    AdvancedView.class_name,
]
AVAILABLE_VIEWS_NAMES: list[str] = [
    GenerateView.CLASS_NAME,
    SearchView.CLASS_NAME,
    DocIndexView.CLASS_NAME,
    AdvancedView.CLASS_NAME,
]
AVAILABLE_VIEWS_UI_NAMES = [
    GenerateView.CLASS_UI_NAME,
    SearchView.CLASS_UI_NAME,
    DocIndexView.CLASS_UI_NAME,
    AdvancedView.CLASS_UI_NAME,
]
AVAILABLE_VIEWS = [
    GenerateView,
    SearchView,
    DocIndexView,
    AdvancedView,
]
