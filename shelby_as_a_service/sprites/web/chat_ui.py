from typing import Any, Dict, List, Optional

import gradio as gr
from services.llm_service import LLMService, OpenAILLM
from sprites.web.gradio_helpers import GRHelper


class ChatUI:
    group_name = "chat_ui"
    comps: Dict[str, Any] = {}
    comps_state: Dict[str, Any] = {}

    def __init__(self, gr_helper: GRHelper):
        # self.vanillm_agent = vanillm_agent
        self.gr_helper = gr_helper
        self.comps["group_name"] = gr.State(self.group_name)
        self.comps["input_chat_textbox"] = gr.State()
        self.comps["stream_chat"] = gr.State(True)
        self.comps["url_input"] = gr.State()
        self.comps["web_data_content"] = gr.State()

    def create_ui(self):
        with gr.Tab("Chat", elem_id="default-tab"):
            with gr.Row():
                self.comps["chat_tab_agent_radios"] = gr.Radio(
                    choices=[
                        "VanillaLLM",
                        "Chat with URL",
                        "Full Context Enhanced Query Pipeline",
                    ],
                    type="index",
                    value="VanillaLLM",
                    show_label=False,
                )
            with gr.Row():
                with gr.Column(scale=4):
                    with gr.Row():
                        self.comps["chat_tab_out_text"] = gr.Textbox(
                            lines=27,
                            label="out_text",
                            show_label=False,
                            interactive=False,
                            elem_id=f"{self.group_name}_chat_tab_out_text",
                        )
                    with gr.Row():
                        self.comps["chat_tab_in_text"] = gr.Textbox(
                            label="in_text",
                            show_label=False,
                            placeholder="Send a message",
                            elem_id=f"{self.group_name}_chat_tab_in_text",
                        )
                    with gr.Row():
                        self.comps["chat_tab_generate_button"] = gr.Button(
                            "Generate", variant="primary"
                        )
                    with gr.Group():
                        with gr.Row():
                            self.comps["chat_tab_in_token_count"] = gr.Textbox(
                                value="Request token count: 0",
                                lines=1,
                                interactive=False,
                                label="Input Token Count",
                                show_label=False,
                            )
                            self.comps["chat_tab_out_token_count"] = gr.Textbox(
                                value="Response token count: 0",
                                lines=1,
                                interactive=False,
                                show_label=False,
                            )
                            self.comps["chat_tab_total_token_count"] = gr.Textbox(
                                value="Total Token Count: 0",
                                lines=1,
                                interactive=False,
                                show_label=False,
                            )
                            self.comps["chat_tab_response_cost"] = gr.Textbox(
                                value="Response price: $0.00",
                                lines=1,
                                interactive=False,
                                show_label=False,
                            )
                            self.comps["chat_tab_total_cost"] = gr.Textbox(
                                value="Total spend: $0.00",
                                lines=1,
                                interactive=False,
                                show_label=False,
                            )
                with gr.Column():
                    with gr.Group():
                        self.comps["chat_llm_provider"] = gr.Dropdown(
                            value=GRHelper.dropdown_default_value(LLMService),
                            choices=GRHelper.dropdown_choices(LLMService),
                            label="LLM Provider",
                        )
                        self.comps["chat_llm_model"] = gr.Dropdown(
                            value=GRHelper.dropdown_default_value(OpenAILLM),
                            choices=GRHelper.dropdown_choices(OpenAILLM),
                            label="LLM Model",
                        )
                    with gr.Group():
                        self.comps["chat_prompts"] = gr.Dropdown(
                            value=GRHelper.dropdown_default_value(OpenAILLM),
                            choices=GRHelper.dropdown_choices(OpenAILLM),
                            label="Prompts",
                        )

        with gr.Tab("Web Data"):
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
            fn=lambda x: (x, ""),
            inputs=self.comps["chat_tab_in_text"],
            outputs=[
                self.comps_state["input_chat_textbox"],
                self.comps["chat_tab_in_text"],
            ],
        ).then(
            fn=self.gr_helper.run_chat,
            inputs=list(self.comps_state.values()),
            outputs=[
                self.comps["chat_tab_out_text"],
                self.comps["chat_tab_in_token_count"],
                self.comps["chat_tab_out_token_count"],
                self.comps["chat_tab_total_token_count"],
            ],
        ).then(
            fn=self.gr_helper.get_spend,
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
            fn=GRHelper.check_url_input,
            inputs=[
                self.comps["web_tab_url_text"],
            ],
            outputs=self.comps_state["url_input"],
        ).success(
            fn=self.gr_helper.load_single_website,
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
