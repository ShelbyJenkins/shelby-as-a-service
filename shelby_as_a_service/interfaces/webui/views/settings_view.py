import typing
from typing import Any, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from pydantic import BaseModel

from shelby_as_a_service.services.service_base import ServiceBase


class SettingsView(ServiceBase):
    CLASS_NAME: str = "settings_view"
    CLASS_UI_NAME: str = "⚙️"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6

    class ClassConfigModel(BaseModel):
        current_ui_view_name: str = "Settings View"

        class Config:
            extra = "ignore"

    config: ClassConfigModel

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        super().__init__(config=config, **kwargs)

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
