from decimal import Decimal
from typing import Any, Dict, List, Optional, Type

import gradio as gr
import sprites.webui.gradio_helpers as GradioHelper
from services.llm_service import LLMService, OpenAILLM


class VanillaLLMUI:
    SETTINGS_PANEL_COL = 2
    CHAT_UI_PANEL_COL = 8
    service: Type

    def __init__(self, webui_sprite) -> None:
        self.webui_sprite = webui_sprite

    @staticmethod
    def create_chat_ui(name):
        components = {}

        with gr.Column(elem_classes="chat_ui_col"):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {name}",
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
                                elem_id=f"{name}_chat_tab_status_text",
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

        return components

    @staticmethod
    def create_settings_ui(agent_instance):
        components = {}

        for service in agent_instance.AVAILABLE_SERVICES:
            service_instance = getattr(agent_instance, service.SERVICE_NAME, None)

        with gr.Column():
            service.create_ui(agent_instance=agent_instance)

        return components

    def create_event_handlers(
        self,
        chat_ui_components,
        chat_ui_components_state,
    ):
        gr.on(
            triggers=[
                chat_ui_components["chat_tab_generate_button"].click,
                chat_ui_components["chat_tab_in_text"].submit,
            ],
            fn=lambda *comp_vals: comp_vals,
            inputs=list(chat_ui_components.values()),
            outputs=list(chat_ui_components_state.values()),
        ).then(
            fn=lambda: "Proooooomptering",
            outputs=chat_ui_components["chat_tab_status_text"],
        ).then(
            fn=self.webui_sprite.run_chat,
            inputs=list(chat_ui_components_state.values()),
            outputs=[
                chat_ui_components["chat_tab_out_text"],
                chat_ui_components["chat_tab_in_token_count"],
                chat_ui_components["chat_tab_out_token_count"],
                chat_ui_components["chat_tab_total_token_count"],
            ],
        ).success(
            fn=lambda: "",
            outputs=chat_ui_components["chat_tab_in_text"],
        ).success(
            fn=self.get_spend,
            outputs=[
                chat_ui_components["chat_tab_response_cost"],
                chat_ui_components["chat_tab_total_cost"],
            ],
        )

    def get_spend(self):
        req = f"Request price: ${round(self.webui_sprite.app.last_request_cost, 4)}"
        self.webui_sprite.app.last_request_cost = Decimal("0")
        tot = f"Total spend: ${round(self.webui_sprite.app.total_cost, 4)}"
        return [req, tot]
