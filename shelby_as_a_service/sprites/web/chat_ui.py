from decimal import Decimal
from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.web.gradio_helpers as GRHelper
from services.llm_service import LLMService, OpenAILLM


class ChatUI:
    group_name = "chat_ui"
    comps: Dict[str, Any] = {}
    comps_state: Dict[str, Any] = {}

    def __init__(self, web_sprite):
        self.web_sprite = web_sprite

        self.comps["group_name"] = gr.State(self.group_name)
        self.comps["input_chat_textbox"] = gr.State()
        self.comps["stream_chat"] = gr.State(True)
        self.comps["url_input"] = gr.State()
        self.comps["web_data_content"] = gr.State()

    def create_ui(self):
        with gr.Tab("Chat", elem_id="default-tab"):
            with gr.Row():
                with gr.Column(scale=5):
                    with gr.Row():
                        self.comps["chat_tab_out_text"] = gr.Textbox(
                            lines=25,
                            label="out_text",
                            show_label=False,
                            interactive=False,
                            elem_id=f"{self.group_name}_chat_tab_out_text",
                        )
                    with gr.Row():
                        self.comps["chat_tab_in_text"] = gr.Textbox(
                            label="in_text",
                            max_lines=3,
                            show_label=False,
                            placeholder="Send a message",
                            elem_id=f"{self.group_name}_chat_tab_in_text",
                        )
                    with gr.Row():
                        self.comps["chat_tab_agent_dropdown"] = gr.Dropdown(
                            value=GRHelper.dropdown_default_value(self.web_sprite),
                            choices=GRHelper.dropdown_choices(self.web_sprite),
                            type="value",
                            label="Generating Chat with:",
                            show_label=True,
                            container=True,
                        )
                        self.comps["chat_tab_generate_button"] = gr.Button(
                            value="Generate",
                            variant="primary",
                            scale=2,
                        )

                    with gr.Accordion(label="Tools", open=False):
                        with gr.Row():
                            self.comps["chat_tab_status_text"] = gr.Textbox(
                                label="status_text",
                                lines=1,
                                max_lines=1,
                                show_label=False,
                                placeholder="...status",
                                elem_id=f"{self.group_name}_chat_tab_status_text",
                            )
                        with gr.Row():
                            self.comps["chat_tab_stop_button"] = gr.Button(
                                value="Stop",
                                variant="primary",
                            )
                            self.comps["chat_tab_reset_button"] = gr.Button(
                                value="Reset",
                                variant="primary",
                            )
                            self.comps["chat_tab_undo_button"] = gr.Button(
                                value="Undo",
                                variant="primary",
                            )
                            self.comps["chat_tab_retry_button"] = gr.Button(
                                value="Retry",
                                variant="primary",
                            )

                    with gr.Accordion(label="Stats", open=False):
                        with gr.Row():
                            self.comps["chat_tab_in_token_count"] = gr.Textbox(
                                value="Request token count: 0",
                                max_lines=1,
                                lines=1,
                                interactive=False,
                                label="Input Token Count",
                                show_label=False,
                            )
                            self.comps["chat_tab_out_token_count"] = gr.Textbox(
                                value="Response token count: 0",
                                max_lines=1,
                                lines=1,
                                interactive=False,
                                show_label=False,
                            )
                            self.comps["chat_tab_total_token_count"] = gr.Textbox(
                                value="Total Token Count: 0",
                                max_lines=1,
                                lines=1,
                                interactive=False,
                                show_label=False,
                            )
                            self.comps["chat_tab_response_cost"] = gr.Textbox(
                                value="Response price: $0.00",
                                max_lines=1,
                                lines=1,
                                interactive=False,
                                show_label=False,
                            )
                            self.comps["chat_tab_total_cost"] = gr.Textbox(
                                value="Total spend: $0.00",
                                max_lines=1,
                                lines=1,
                                interactive=False,
                                show_label=False,
                            )

                with gr.Column():
                    with gr.Accordion(label="Past Chats", open=False):
                        self.comps["chat_tab_history_dropdown"] = gr.Dropdown(
                            value=GRHelper.dropdown_default_value(OpenAILLM),
                            choices=GRHelper.dropdown_choices(OpenAILLM),
                            label="Chats",
                            container=True,
                        )
                        self.comps["chat_tab_history_button"] = gr.Button(
                            "Load Chat",
                            variant="primary",
                            size="sm",
                        )
                    with gr.Accordion(label="Prompt Templates", open=False):
                        self.comps["chat_tab_prompts_dropdown"] = gr.Dropdown(
                            value=GRHelper.dropdown_default_value(OpenAILLM),
                            choices=GRHelper.dropdown_choices(OpenAILLM),
                            label="Prompts",
                            container=True,
                        )
                        self.comps["chat_tab_prompts_button"] = gr.Button(
                            "Load Template", variant="primary", size="sm"
                        )
                    with gr.Accordion(label="LLM Settings"):
                        self.comps["chat_llm_provider"] = gr.Dropdown(
                            value=GRHelper.dropdown_default_value(LLMService),
                            choices=GRHelper.dropdown_choices(LLMService),
                            label="LLM Provider",
                            container=True,
                        )
                        self.comps["chat_llm_model"] = gr.Dropdown(
                            value=GRHelper.dropdown_default_value(OpenAILLM),
                            choices=GRHelper.dropdown_choices(OpenAILLM),
                            label="LLM Model",
                            container=True,
                        )
                        with gr.Accordion(label="Advanced Settings", open=False):
                            self.comps["chat_llm_advanced"] = gr.Dropdown(
                                value=GRHelper.dropdown_default_value(OpenAILLM),
                                choices=GRHelper.dropdown_choices(OpenAILLM),
                                label="LLM Model",
                                container=True,
                            )

        with gr.Tab("Add Context Data"):
            with gr.Group():
                with gr.Row(variant="compact"):
                    self.comps["web_tab_url_text"] = gr.Textbox(
                        label="url_text",
                        show_label=False,
                        max_lines=1,
                        lines=1,
                        placeholder="Enter URL",
                        elem_id=f"{self.group_name}_web_tab_url_text",
                    )
                with gr.Row(variant="compact"):
                    with gr.Column():
                        self.comps["web_tab_enter_url_button"] = gr.Button(
                            "Load URL", variant="primary", size="sm"
                        )
            with gr.Row():
                with gr.Column(scale=4):
                    with gr.Row():
                        self.comps["web_data_text_out"] = gr.Textbox(
                            lines=27,
                            label="web_data_text_out",
                            show_label=False,
                            interactive=False,
                            elem_id=f"{self.group_name}_web_data_text_out",
                        )
                with gr.Column():
                    self.comps["tbd_settings1"] = gr.Dropdown(
                        choices=GRHelper.dropdown_default_value(LLMService),
                        value=GRHelper.dropdown_choices(OpenAILLM),
                        label="tbd_settings1",
                    )
                    self.comps["tbd_settings2"] = gr.Dropdown(
                        choices=GRHelper.dropdown_default_value(LLMService),
                        value=GRHelper.dropdown_choices(OpenAILLM),
                        label="tbd_settings2",
                    )

        with gr.Tab("History", elem_id="default-tab"):
            with gr.Row():
                with gr.Column(scale=4):
                    with gr.Row():
                        self.comps["history"] = gr.Textbox(
                            lines=27,
                            label="history",
                            show_label=False,
                            interactive=False,
                            elem_id=f"{self.group_name}_history",
                            value="tbd",
                        )
        with gr.Tab("Prompt Templates", elem_id="default-tab"):
            with gr.Row():
                with gr.Column(scale=4):
                    with gr.Row():
                        self.comps["prompt_templates"] = gr.Textbox(
                            lines=27,
                            label="prompt_templates",
                            show_label=False,
                            interactive=False,
                            elem_id=f"{self.group_name}_prompt_templates",
                            value="tbd",
                        )
        with gr.Tab("Help", elem_id="default-tab"):
            with gr.Row():
                with gr.Column(scale=4):
                    with gr.Row():
                        self.comps["help"] = gr.Textbox(
                            lines=27,
                            label="help",
                            show_label=False,
                            interactive=False,
                            elem_id=f"{self.group_name}_help",
                            value="tbd",
                        )

        self.comps_state = {k: gr.State(None) for k in self.comps.keys()}

        self.event_handlers()

        return {"comps": self.comps, "comps_state": self.comps_state}

    def event_handlers(self):
        gr.on(
            triggers=[
                self.comps["chat_tab_generate_button"].click,
                self.comps["chat_tab_in_text"].submit,
            ],
            fn=lambda *comp_vals: comp_vals,
            inputs=list(self.comps.values()),
            outputs=list(self.comps_state.values()),
        ).then(
            fn=lambda x: x,
            inputs=self.comps["chat_tab_in_text"],
            outputs=self.comps_state["input_chat_textbox"],
        ).then(
            fn=lambda: "Proooooomptering",
            outputs=self.comps["chat_tab_status_text"],
        ).then(
            fn=self.web_sprite.run_chat,
            inputs=list(self.comps_state.values()),
            outputs=[
                self.comps["chat_tab_out_text"],
                self.comps["chat_tab_in_token_count"],
                self.comps["chat_tab_out_token_count"],
                self.comps["chat_tab_total_token_count"],
            ],
        ).success(
            fn=lambda: "",
            outputs=self.comps["chat_tab_in_text"],
        ).success(
            fn=self.get_spend,
            outputs=[
                self.comps["chat_tab_response_cost"],
                self.comps["chat_tab_total_cost"],
            ],
        )

        # Add Web Data from URL
        gr.on(
            triggers=[
                self.comps["web_tab_url_text"].submit,
                self.comps["web_tab_enter_url_button"].click,
            ],
            fn=lambda *comp_vals: comp_vals,
            inputs=list(self.comps.values()),
            outputs=list(self.comps_state.values()),
        ).then(
            fn=self.web_sprite.load_single_website,
            inputs=list(self.comps_state.values()),
            outputs=[
                self.comps["web_data_text_out"],
                self.comps["web_data_content"],
            ],
        ).success(
            fn=lambda: "",
            outputs=[
                self.comps["web_tab_url_text"],
            ],
        )

        # Outputs agent_select_status_message to status bar when agent selected
        self.comps["chat_tab_agent_dropdown"].change(
            fn=self.agent_select_status_message,
            inputs=self.comps["chat_tab_agent_dropdown"],
            outputs=self.comps["chat_tab_status_text"],
        )

    def agent_select_status_message(self, chat_tab_agent_dropdown):
        agent = self.web_sprite.get_selected_agent(chat_tab_agent_dropdown)
        if message := getattr(agent, "agent_select_status_message", None):
            return message
        raise gr.Error("Bad value for agent_select_status_message!")

    def get_spend(self):
        req = f"Request price: ${round(self.web_sprite.app.last_request_cost, 4)}"
        self.web_sprite.app.last_request_cost = Decimal("0")
        tot = f"Total spend: ${round(self.web_sprite.app.total_cost, 4)}"
        return [req, tot]
