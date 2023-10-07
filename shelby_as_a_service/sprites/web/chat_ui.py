from decimal import Decimal
from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.web.gradio_helpers as GradioHelper
from services.llm_service import LLMService, OpenAILLM


class ChatUI:
    def __init__(self, web_sprite):
        self.web_sprite = web_sprite
        self.features = self.web_sprite.ui["features"]

    def create_chat_ui(self):
        def creator(agent):
            name = GradioHelper.get_class_name(agent)
            ui_name = GradioHelper.get_class_ui_name(agent)
            class_instance = getattr(self.web_sprite, name, None)

            if ui_name == self.web_sprite.config.current_feature_ui_name:
                visibility = True
            else:
                visibility = False

            with gr.Row(
                elem_classes="chat_ui_feature_row",
                elem_id=f"{name}_chat_ui_row",
                visible=visibility,
            ) as self.features[name]["chat_ui_row"]:
                match name:
                    case "vanillallm_agent":
                        self.features[name]["chat_ui"] = self.create_vanillallm_agent(
                            name, class_instance
                        )
                    case "ceq_agent":
                        self.features[name]["chat_ui"] = self.create_vanillallm_agent(
                            name, class_instance
                        )
                    case "web_agent":
                        self.features[name]["chat_ui"] = self.create_vanillallm_agent(
                            name, class_instance
                        )

        for agent in self.web_sprite.AVAILABLE_AGENTS:
            creator(agent)

    def create_vanillallm_agent(self, name, feature_class):
        components: Dict[str, Any] = {}
        components_state: Dict[str, Any] = {}
        components["feature_name"] = gr.State(name)
        components["input_chat_textbox"] = gr.State()
        components["stream_chat"] = gr.State(True)

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

        components_state = {k: gr.State(None) for k in components.keys()}
        self.features[name]["settings_tab"]["components"]
        self.event_handlers(
            components,
            self.features[name]["settings_tab"]["components"],
            components_state,
            self.features[name]["settings_tab"]["components_state"],
        )

        return {
            "components": components,
            "components_state": components_state,
        }

    def event_handlers(
        self,
        components,
        settings_components,
        components_state,
        settings_components_state,
    ):
        merged_components = list(components.values()) + list(
            settings_components.values()
        )
        merged_components_state = list(components_state.values()) + list(
            settings_components_state.values()
        )

        gr.on(
            triggers=[
                # components["chat_tab_generate_button"].click,
                components["chat_tab_in_text"].submit,
            ],
            fn=lambda *comp_vals: comp_vals,
            inputs=merged_components,
            outputs=merged_components_state,
        ).then(
            fn=lambda x: x,
            inputs=components["chat_tab_in_text"],
            outputs=components_state["input_chat_textbox"],
        ).then(
            fn=lambda: "Proooooomptering",
            outputs=components["chat_tab_status_text"],
        ).then(
            fn=self.web_sprite.run_chat,
            inputs=list(components_state.values()),
            outputs=[
                components["chat_tab_out_text"],
                components["chat_tab_in_token_count"],
                components["chat_tab_out_token_count"],
                components["chat_tab_total_token_count"],
            ],
        ).success(
            fn=lambda: "",
            outputs=components["chat_tab_in_text"],
        ).success(
            fn=self.get_spend,
            outputs=[
                components["chat_tab_response_cost"],
                components["chat_tab_total_cost"],
            ],
        )

    def get_spend(self):
        req = f"Request price: ${round(self.web_sprite.app.last_request_cost, 4)}"
        self.web_sprite.app.last_request_cost = Decimal("0")
        tot = f"Total spend: ${round(self.web_sprite.app.total_cost, 4)}"
        return [req, tot]
