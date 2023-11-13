import typing
from typing import Any, Literal, Optional, Type, get_args

import gradio as gr
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase


class SettingsView(GradioBase):
    class_name = Literal["settings_view"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "⚙️"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6

    class ClassConfigModel(BaseModel):
        current_ui_view_name: str = "Settings View"

        class Config:
            extra = "ignore"

    config: ClassConfigModel

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def create_primary_ui(self):
        components = {}

        with gr.Column(elem_classes="primary_ui_col"):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {SettingsView.CLASS_UI_NAME}",
                elem_id="chat_tab_out_text",
                elem_classes="chat_tab_out_text_class",
                scale=7,
            )

    def create_settings_ui(self):
        with gr.Column():
            gr.Textbox(value="To Implement")
