from decimal import Decimal
from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.webui.gradio_helpers as GradioHelper
from services.llm_service import LLMService, OpenAILLM


class CEQUI:
    SETTINGS_PANEL_COL = 3
    CHAT_UI_PANEL_COL = 7

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
                    )
                    components["chat_tab_reset_button"] = gr.Button(
                        value="Reset",
                        variant="primary",
                    )
                    components["chat_tab_undo_button"] = gr.Button(
                        value="Undo",
                        variant="primary",
                    )
                    components["chat_tab_retry_button"] = gr.Button(
                        value="Retry",
                        variant="primary",
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
    def create_settings_ui(name, agent_instance):
        components: Dict[str, Any] = {}

        with gr.Accordion(label="Past Chats", open=False):
            components["chat_tab_history_dropdown"] = gr.Dropdown(
                value=None,
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="Chats",
                container=True,
            )
            components["chat_tab_history_button"] = gr.Button(
                "Load Chat",
                variant="primary",
                size="sm",
            )
        with gr.Accordion(label="Prompt Templates", open=False):
            components["chat_tab_prompts_dropdown"] = gr.Dropdown(
                value=None,
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="Prompts",
                container=True,
            )
            components["chat_tab_prompts_button"] = gr.Button(
                "Load Template", variant="primary", size="sm"
            )
        with gr.Accordion(label="LLM Settings"):
            components["llm_provider"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(agent_instance, LLMService),
                choices=GradioHelper.dropdown_choices(LLMService),
                label="LLM Provider",
                container=True,
            )
            components["llm_model"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(agent_instance, OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="LLM Model",
                container=True,
            )
        with gr.Accordion(label="Advanced Settings", open=False):
            components["chat_llm_advanced"] = gr.Dropdown(
                value=None,
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="LLM Model",
                container=True,
            )
        components["chat_tab_generate_button"] = gr.Button(
            value="Generate",
            variant="primary",
            scale=2,
        )

        return components
