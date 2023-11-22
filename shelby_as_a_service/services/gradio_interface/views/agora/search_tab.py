import typing
from typing import Any, Literal, Optional, Type, get_args

import gradio as gr
from pydantic import BaseModel
from services.document_loading.document_loading_service import DocLoadingService
from services.gradio_interface.gradio_base import GradioBase
from services.text_processing.ingest_processing.ingest_processing_service import (
    IngestProcessingService,
)


class SearchTab(GradioBase):
    class_name = Literal["search_tab"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Search"

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def create_tab_ui(self):
        components = {}
        with gr.Row(equal_height=True):
            with gr.Accordion(label="Advanced", open=False):
                (
                    doc_loaders_dd,
                    doc_loader_components_dict,
                ) = DocLoadingService.create_doc_index_ui_components(
                    parent_instance=self.doc_index.domain,
                    groups_rendered=False,
                )
        with gr.Row(elem_classes="agora_ui_textbox"):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                placeholder=f"Your search results will appear here.",
                elem_id="chat_tab_out_text",
                max_lines=60,
                lines=10,
                interactive=False,
            )
        with gr.Row(equal_height=True):
            components["chat_tab_in_text"] = gr.Textbox(
                lines=2,
                max_lines=5,
                show_label=False,
                placeholder="Query, or URI",
                autofocus=True,
            )

        with gr.Row(equal_height=True):
            components["generate_button"] = gr.Button(
                value="Search",
                variant="primary",
                min_width=0,
                scale=2,
            )
            gr.Radio(
                show_label=False,
                choices=["URL from Web", "Local Docs", "Custom"],
                scale=3,
            )
            components["chat_tab_stop_button"] = gr.Button(
                value="Stop",
                variant="stop",
                # elem_classes="action_button",
                min_width=0,
                scale=1,
            )
            components["chat_tab_reset_button"] = gr.Button(
                value="Clear",
                variant="primary",
                # elem_classes="action_button",
                min_width=0,
                scale=1,
            )
            components["chat_tab_retry_button"] = gr.Button(
                value="Retry",
                variant="primary",
                # elem_classes="action_button",
                min_width=0,
                scale=1,
            )

        return components
