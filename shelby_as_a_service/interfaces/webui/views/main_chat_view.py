from decimal import Decimal
from typing import Any, Dict, List, Optional, Type

import gradio as gr
from app_config.app_base import AppBase


class MainChatView(AppBase):
    MODULE_NAME: str = "main_chat_view"
    MODULE_UI_NAME: str = "Main Chat"
    SETTINGS_UI_COL = 2
    PRIMARY_UI_COL = 8

    def __init__(self, webui_sprite):
        self.webui_sprite = webui_sprite
        self.vanillallm_agent = self.webui_sprite.vanillallm_agent

    def create_primary_ui(self):
        components = {}

        with gr.Column(elem_classes="primary_ui_col"):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {MainChatView.MODULE_UI_NAME}",
                elem_id="chat_tab_out_text",
                elem_classes="chat_tab_out_text_class",
                scale=7,
            )

            components["chat_tab_in_text"] = gr.Textbox(
                show_label=False,
                placeholder="Send a message",
                elem_id="chat_tab_in_text",
                elem_classes="chat_tab_in_text_class",
                scale=3,
            )

            with gr.Row():
                with gr.Column(
                    min_width=0,
                ):
                    components["chat_tab_generate_button"] = gr.Button(
                        value="Generate",
                        variant="primary",
                        elem_classes="chat_tab_button",
                        min_width=0,
                    )
                with gr.Column(scale=3):
                    with gr.Accordion(label="Tools", open=False, visible=True):
                        with gr.Row():
                            components["chat_tab_status_text"] = gr.Textbox(
                                label="status_text",
                                lines=1,
                                max_lines=1,
                                show_label=False,
                                placeholder="...status",
                                elem_id=f"{MainChatView.MODULE_NAME}_chat_tab_status_text",
                            )
                        with gr.Row():
                            components["chat_tab_stop_button"] = gr.Button(
                                value="Stop",
                                variant="primary",
                                elem_classes="chat_tab_button",
                                min_width=0,
                            )
                            components["chat_tab_reset_button"] = gr.Button(
                                value="Reset",
                                variant="primary",
                                elem_classes="chat_tab_button",
                                min_width=0,
                            )
                            components["chat_tab_undo_button"] = gr.Button(
                                value="Undo",
                                variant="primary",
                                elem_classes="chat_tab_button",
                                min_width=0,
                            )
                            components["chat_tab_retry_button"] = gr.Button(
                                value="Retry",
                                variant="primary",
                                elem_classes="chat_tab_button",
                                min_width=0,
                            )

                        with gr.Accordion(label="Stats", open=False):
                            with gr.Row():
                                components["chat_tab_in_token_count"] = gr.Textbox(
                                    value="Request token count: 0",
                                    max_lines=1,
                                    lines=1,
                                    interactive=False,
                                    label="Input Token Count",
                                    show_label=False,
                                )
                                components["chat_tab_out_token_count"] = gr.Textbox(
                                    value="Response token count: 0",
                                    max_lines=1,
                                    lines=1,
                                    interactive=False,
                                    show_label=False,
                                )
                                components["chat_tab_total_token_count"] = gr.Textbox(
                                    value="Total Token Count: 0",
                                    max_lines=1,
                                    lines=1,
                                    interactive=False,
                                    show_label=False,
                                )
                                components["chat_tab_response_cost"] = gr.Textbox(
                                    value="Response price: $0.00",
                                    max_lines=1,
                                    lines=1,
                                    interactive=False,
                                    show_label=False,
                                )
                                components["chat_tab_total_cost"] = gr.Textbox(
                                    value="Total spend: $0.00",
                                    max_lines=1,
                                    lines=1,
                                    interactive=False,
                                    show_label=False,
                                )

        self.create_event_handlers(components)

        return components

    def create_settings_ui(self):
        with gr.Column():
            for module_instance in self.vanillallm_agent.required_module_instances:
                module_instance.create_settings_ui()

    def create_event_handlers(self, components):
        def get_spend():
            req = f"Request price: ${round(AppBase.last_request_cost, 4)}"
            AppBase.last_request_cost = Decimal("0")
            tot = f"Total spend: ${round(AppBase.total_cost, 4)}"
            return [req, tot]

        gr.on(
            triggers=[
                components["chat_tab_generate_button"].click,
                components["chat_tab_in_text"].submit,
            ],
            fn=lambda: "Proooooomptering",
            outputs=components["chat_tab_status_text"],
        ).then(
            fn=self.vanillallm_agent.run_chat,
            inputs=components["chat_tab_in_text"],
            outputs=[
                components["chat_tab_out_text"],
                components["chat_tab_in_token_count"],
                components["chat_tab_out_token_count"],
                components["chat_tab_total_token_count"],
            ],
        ).success(
            fn=lambda: "",
            outputs=components["chat_tab_in_text"],
        ).then(
            fn=get_spend,
            outputs=[
                components["chat_tab_response_cost"],
                components["chat_tab_total_cost"],
            ],
        )
