import typing
from decimal import Decimal
from typing import Any, Literal, Optional, Type, get_args

import agents as agents
import gradio as gr
from app.config_manager import ConfigManager
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase


class ClassConfigModel(BaseModel):
    current_agent_name: str = "vanillallm_agent"
    current_agent_ui_name: str = "VanillaLLM Agent"
    chat_tab_enabled_ceq_checkbox: bool = False

    class Config:
        extra = "ignore"


class GenerateView(GradioBase):
    class_name = Literal["generate_view"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Generate"
    SETTINGS_UI_COL = 2
    PRIMARY_UI_COL = 8
    REQUIRED_CLASSES: list[Type] = agents.AVAILABLE_AGENTS
    AVAILABLE_AGENTS_TYPINGS = agents.AVAILABLE_AGENTS_TYPINGS
    AVAILABLE_AGENTS_UI_NAMES: list[str] = agents.AVAILABLE_AGENTS_UI_NAMES

    class_config_model = ClassConfigModel
    config: ClassConfigModel
    ceq_agent: agents.CEQAgent

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        if self.list_of_required_class_instances:
            self.list_of_agent_instances: list[
                agents.CEQAgent
            ] = self.list_of_required_class_instances
            self.current_agent_instance: agents.CEQAgent = self.get_requested_class(
                requested_class=self.config.current_agent_name,
                available_classes=self.REQUIRED_CLASSES,
            )

    def set_view_event_handlers(self):
        pass

    def run_chat(self, chat_in):
        self.log.info(f"Running query: {chat_in}")

        generate_view_config = ConfigManager.get_config(
            app_name=self.app_config.app_name, path=["webui_sprite", "gradio_ui", "generate_view"]
        )
        ceq_agent = agents.CEQAgent(config_file_dict=generate_view_config)

        if self.config.chat_tab_enabled_ceq_checkbox:
            response = ceq_agent.create_ceq_chat(
                chat_in=chat_in,
            )
        else:
            response = ceq_agent.create_vanilla_chat(
                chat_in=chat_in,
            )
        yield from response

    def create_primary_ui(self):
        components = {}

        with gr.Column(elem_classes="primary_ui_col"):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {GenerateView.CLASS_UI_NAME}",
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
                                elem_id=f"{GenerateView.CLASS_NAME}_chat_tab_status_text",
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
        components = {}

        with gr.Column():
            with gr.Tab(label=self.ceq_agent.CLASS_UI_NAME):
                components["chat_tab_enabled_ceq_checkbox"] = gr.Checkbox(
                    label="Enable CEQ Agent",
                    value=False,
                    elem_id="chat_tab_enabled_ceq_checkbox",
                )
                self.ceq_agent.create_main_chat_ui()
            with gr.Tab(label=self.ceq_agent.llm_service.CLASS_UI_NAME):
                self.ceq_agent.llm_service.create_settings_ui()

        GradioBase.create_settings_event_listener(self.config, components)

    def create_event_handlers(self, components):
        def get_spend():
            req = f"Request price: ${round(self.last_request_cost, 4)}"
            self.last_request_cost = Decimal("0")
            tot = f"Total spend: ${round(self.total_cost, 4)}"
            return [req, tot]

        gr.on(
            triggers=[
                components["chat_tab_generate_button"].click,
                components["chat_tab_in_text"].submit,
            ],
            fn=lambda: "Proooooomptering",
            outputs=components["chat_tab_status_text"],
        ).then(
            fn=self.run_chat,
            inputs=components["chat_tab_in_text"],
            outputs=[
                components["chat_tab_out_text"],
            ],
        ).success(
            fn=lambda: "",
            outputs=components["chat_tab_in_text"],
        )

        # components["chat_tab_in_token_count"],
        # components["chat_tab_out_token_count"],
        # components["chat_tab_total_token_count"],
        # ).then(
        #     fn=get_spend,
        #     outputs=[
        #         components["chat_tab_response_cost"],
        #         components["chat_tab_total_cost"],
        #     ],
        # )
