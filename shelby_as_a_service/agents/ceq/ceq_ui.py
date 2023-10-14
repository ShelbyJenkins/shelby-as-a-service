from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper


class CEQUI:
    MODULE_NAME: str = "ceq_agent"
    MODULE_UI_NAME: str = "Context Enhanced Querying"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6

    service: Type

    @classmethod
    def create_primary_ui(cls, agent_instance):
        components = {}

        with gr.Column(elem_classes="primary_ui_col"):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {CEQUI.MODULE_UI_NAME}",
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
                                elem_id=f"{agent_instance.MODULE_NAME}_chat_tab_status_text",
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

        cls.create_event_handlers(agent_instance, components)

        return components

    @staticmethod
    def create_settings_ui(agent_instance):
        with gr.Column():
            for service in agent_instance.REQUIRED_MODULES:
                service_instance = getattr(agent_instance, service.MODULE_NAME, None)
                service_instance.create_settings_ui()

    @classmethod
    def create_event_handlers(cls, agent_instance, components):
        def get_spend():
            req = f"Request price: ${round(agent_instance.last_request_cost, 4)}"
            agent_instance.last_request_cost = Decimal("0")
            tot = f"Total spend: ${round(agent_instance.total_cost, 4)}"
            return [req, tot]

        gr.on(
            triggers=[
                components["chat_tab_generate_button"].click,
                components["chat_tab_in_text"].submit,
            ],
            fn=lambda: "Proooooomptering",
            outputs=components["chat_tab_status_text"],
        ).then(
            fn=agent_instance.run_chat,
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
