from __future__ import annotations

from typing import Any, Literal, Optional, Type, get_args

import gradio as gr
import services.gradio_interface.views.agora as agora_tabs
from services.gradio_interface.gradio_base import GradioBase


class AgoraView(GradioBase):
    class_name = Literal["agora_view"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Agora"
    REQUIRED_CLASSES: list[Type] = agora_tabs.AVAILABLE_CLASSES
    AVAILABLE_CLASSES_UI_NAMES: list[str] = agora_tabs.AVAILABLE_CLASSES_UI_NAMES

    list_of_class_instances: list[
        agora_tabs.GenerateTab | agora_tabs.SearchTab | agora_tabs.EditTab
    ]

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.list_of_class_instances = self.list_of_required_class_instances

    def create_view_ui(self):
        with gr.Row(elem_classes="view_ui_row"):
            with gr.Column(scale=9):
                with gr.Tabs(elem_classes="agora_ui_tabs"):
                    for tab in self.list_of_class_instances:
                        with gr.Tab(
                            id=tab.CLASS_NAME,
                            label=tab.CLASS_UI_NAME,
                            elem_classes="agora_ui_tab",
                        ) as agent_nav_tab:
                            tab.create_tab_ui()
            with gr.Column(scale=1):
                gr.Textbox(
                    lines=50,
                    show_label=False,
                    placeholder="Query, or URI",
                    autofocus=True,
                    min_width=0,
                )

    @property
    def view_css(self) -> str:
        return """
            .agora_ui_tabs {
                display: flex;
                flex-direction: column;
                height: 100%;
                box-sizing: border-box;
            }
            .agora_ui_tab {
                display: flex;
                flex-direction: column;
                height: 96%;
                box-sizing: border-box;
            }
            .agora_ui_tab_row {
                display: flex;
                flex-direction: row;
                height: 99%;
                box-sizing: border-box;
            }

            """
        # .agora_ui_textbox_row {
        #     display: flex;
        #     box-sizing: border-box;
        #     height: 99%;
        #     flex-direction: column;
        # }

        # .agora_ui_tab > first-child {
        #     display: flex;
        #     flex-direction: column;
        #     height: 99%;
        #     box-sizing: border-box;
        # }
        # .agora_ui_textbox label {
        #     resize: none;
        #     height: 100%;
        # }
        # .agora_ui_textbox label textarea {
        #     resize: none;
        #     height: 100%;
        #     scrollbar-width: thin;
        # }
        # .agora_ui_textbox label textarea::-webkit-scrollbar {
        #     width: 8px;
