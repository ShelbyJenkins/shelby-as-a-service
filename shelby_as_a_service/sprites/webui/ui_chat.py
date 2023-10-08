from decimal import Decimal
from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.webui.gradio_helpers as GradioHelper


class UIChat:
    def __init__(self, webui_sprite):
        self.webui_sprite = webui_sprite
        self.gradio_agents = self.webui_sprite.gradio_ui["gradio_agents"]

    def create_chat_ui(self):
        def creator(agent):
            name = GradioHelper.get_class_name(agent)
            ui_name = GradioHelper.get_class_ui_name(agent)
            class_instance = getattr(self.webui_sprite, name, None)
            existing_ui_dict = self.gradio_agents[name].get("ui", {})
            if ui_name == self.webui_sprite.config.current_agent_ui_name:
                visibility = True
            else:
                visibility = False

            with gr.Row(
                elem_classes="chat_ui_feature_row",
                elem_id=f"{name}_chat_ui_row",
                visible=visibility,
            ) as chat_ui_row:
                match name:
                    case "vanillallm_agent":
                        components = self.create_vanillallm_agent(name, class_instance)
                    case "ceq_agent":
                        components = self.create_vanillallm_agent(name, class_instance)
                    case "web_agent":
                        components = self.create_vanillallm_agent(name, class_instance)
                    case _:
                        components = {}

            self.gradio_agents[name]["chat_ui_row"] = chat_ui_row

            self.gradio_agents[name][
                "ui"
            ] = GradioHelper.merge_feature_components_and_create_state(
                existing_ui_dict, components
            )

        for agent in self.webui_sprite.AVAILABLE_AGENTS:
            creator(agent)

    def create_vanillallm_agent(self, name, feature_class):
        components: Dict[str, Any] = {}

        with gr.Column(
            elem_classes="chat_ui_feature_col",
        ):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {name}",
                elem_id="chat_tab_out_text",
                elem_classes="chat_tab_out_text_class",
            )

            components["chat_tab_in_text"] = gr.Textbox(
                show_label=False,
                placeholder="Send a message",
                elem_id="chat_tab_in_text",
                elem_classes="chat_tab_in_text_class",
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
