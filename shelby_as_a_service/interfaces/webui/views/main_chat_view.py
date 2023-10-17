from decimal import Decimal
from typing import Any, Dict, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from agents.ceq.ceq_agent import CEQAgent
from agents.vanillallm.vanillallm_agent import VanillaLLM
from app_config.module_base import ModuleBase
from pydantic import BaseModel


class MainChatView(ModuleBase):
    MODULE_NAME: str = "main_chat_view"
    MODULE_UI_NAME: str = "Main Chat"
    SETTINGS_UI_COL = 2
    PRIMARY_UI_COL = 8
    REQUIRED_MODULES: list[Type] = [VanillaLLM, CEQAgent]

    class ModuleConfigModel(BaseModel):
        current_agent_name: str = "vanillallm_agent"
        current_agent_ui_name: str = "VanillaLLM Agent"

        class Config:
            extra = "ignore"

    config: ModuleConfigModel
    list_of_module_ui_names: list
    list_of_module_instances: list
    vanillallm_agent: Any
    current_agent_instance: Any

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(
            module_instance=self, config_file_dict=config_file_dict, **kwargs
        )

        self.current_agent_instance = self.get_requested_module_instance(
            self.list_of_module_instances, self.config.current_agent_name
        )

    def run_chat(self, chat_in):
        self.log.print_and_log(f"Running query: {chat_in}")

        response = self.current_agent_instance.run_chat(
            chat_in=chat_in,
        )
        yield from response
        return None

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
        components = {}

        with gr.Column():
            agent_radio = gr.Radio(
                value=self.config.current_agent_ui_name,
                choices=self.list_of_module_ui_names,
            )

            agent_settings_list = []

            for agent_instance in self.list_of_module_instances:
                ui_name = agent_instance.MODULE_UI_NAME
                if ui_name == self.config.current_agent_ui_name:
                    visibility = True
                else:
                    visibility = False
                with gr.Accordion(
                    label=agent_instance.MODULE_UI_NAME, open=True, visible=visibility
                ) as agent_settings:
                    for module_instance in agent_instance.list_of_module_instances:
                        module_instance.create_settings_ui()

                agent_settings_list.append(agent_settings)

        def set_current_agent(requsted_agent):
            output = []
            for module_instance in self.list_of_module_instances:
                ui_name = module_instance.MODULE_UI_NAME
                if ui_name == requsted_agent:
                    self.config.current_agent_name = module_instance.MODULE_NAME
                    self.config.current_agent_ui_name = ui_name
                    self.current_agent_instance = module_instance
                    ModuleBase.update_settings_file = True
                    output.append(gr.Accordion(label=ui_name, visible=True))
                else:
                    output.append(gr.Accordion(label=ui_name, visible=False))
            return output

        agent_radio.change(
            fn=set_current_agent,
            inputs=agent_radio,
            outputs=agent_settings_list,
        )

        GradioHelper.create_settings_event_listener(self, components)

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
