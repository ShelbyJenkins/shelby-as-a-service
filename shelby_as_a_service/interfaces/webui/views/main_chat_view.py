from decimal import Decimal
from typing import Any, Dict, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from agents.ceq.ceq_agent import CEQAgent
from agents.vanillallm.vanillallm_agent import VanillaLLM
from app.module_base import ModuleBase
from pydantic import BaseModel


class MainChatView(ModuleBase):
    CLASS_NAME: str = "main_chat_view"
    CLASS_UI_NAME: str = "Chat"
    SETTINGS_UI_COL = 2
    PRIMARY_UI_COL = 8
    REQUIRED_CLASSES: list[Type] = [VanillaLLM, CEQAgent]

    class ClassConfigModel(BaseModel):
        current_agent_name: str = "vanillallm_agent"
        current_agent_ui_name: str = "VanillaLLM Agent"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_names: list
    list_of_class_ui_names: list
    list_of_class_instances: list
    vanillallm_agent: Any
    current_agent_instance: Any

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

        self.current_agent_instance = self.get_requested_class_instance(
            self.list_of_class_instances, self.config.current_agent_name
        )

    def run_chat(self, chat_in):
        self.log.info(f"Running query: {chat_in}")

        response = self.current_agent_instance.run_chat(
            chat_in=chat_in,
        )
        yield from response

    def create_primary_ui(self):
        components = {}

        with gr.Column(elem_classes="primary_ui_col"):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {MainChatView.CLASS_UI_NAME}",
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
                                elem_id=f"{MainChatView.CLASS_NAME}_chat_tab_status_text",
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
            agent_settings_list = []
            self.config.current_agent_ui_name
            for agent_instance in self.list_of_class_instances:
                with gr.Tab(label=agent_instance.CLASS_UI_NAME) as agent_settings:
                    agent_instance.create_settings_ui()

                agent_settings_list.append(agent_settings)

        def create_nav_events(agent_settings_list):
            def set_agent_view(requested_agent: str):
                for agent in self.list_of_class_instances:
                    if requested_agent == agent.CLASS_UI_NAME:
                        self.config.current_agent_name = agent.CLASS_NAME
                        self.config.current_agent_ui_name = agent.CLASS_UI_NAME
                        self.current_agent_instance = agent

                ModuleBase.update_settings_file = True

            def get_nav_evt(evt: gr.SelectData):
                output = set_agent_view(evt.value)
                return output

            for agent_nav_tab in agent_settings_list:
                agent_nav_tab.select(
                    fn=get_nav_evt,
                )

        create_nav_events(agent_settings_list)

        GradioHelper.create_settings_event_listener(self.config, components)

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
