import typing
from typing import Any, Literal, Optional, Type, get_args

import gradio as gr
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase


class SearchView(GradioBase):
    class_name = Literal["search_view"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Search"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def set_view_event_handlers(self):
        pass

    def create_primary_ui(self):
        pass

    def create_settings_ui(self):
        pass
