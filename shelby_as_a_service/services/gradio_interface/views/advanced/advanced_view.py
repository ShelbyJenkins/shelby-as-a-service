import typing
from typing import Any, Literal, Optional, Type, get_args

import gradio as gr
from services.gradio_interface.gradio_base import GradioBase


class AdvancedView(GradioBase):
    class_name = Literal["advanced_view"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Advanced"

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def create_view_ui(self):
        components = {}

        with gr.Column():
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {AdvancedView.CLASS_UI_NAME}",
                elem_id="chat_tab_out_text",
                elem_classes="chat_tab_out_text_class",
                scale=7,
            )

    @property
    def view_css(self) -> str:
        return ""
