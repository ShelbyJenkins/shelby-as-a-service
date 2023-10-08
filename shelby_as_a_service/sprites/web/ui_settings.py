from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.web.gradio_helpers as GradioHelper
from services.llm_service import LLMService, OpenAILLM


class UISettings:
    def __init__(self, web_sprite) -> None:
        self.web_sprite = web_sprite
        self.features = self.web_sprite.ui["features"]

    def create_settings_panel(self):
        def creator(agent):
            name = GradioHelper.get_class_name(agent)
            class_instance = getattr(self.web_sprite, name, None)
            ui_name = GradioHelper.get_class_ui_name(agent)
            existing_ui_dict = self.features[name].get("ui", {})

            with gr.Tab(
                label=ui_name,
                elem_id=f"{name}_settings_tab_component",
            ) as settings_tab_component:
                match name:
                    case "vanillallm_agent":
                        components = self.create_vanillallm_agent_settings(
                            name, class_instance
                        )
                    case "ceq_agent":
                        components = self.create_vanillallm_agent_settings(
                            name, class_instance
                        )
                    case "web_agent":
                        components = self.create_vanillallm_agent_settings(
                            name, class_instance
                        )
                    case _:
                        components = {}

                self.features[name]["settings_tab_component"] = settings_tab_component

                self.features[name][
                    "ui"
                ] = GradioHelper.merge_feature_components_and_create_state(
                    existing_ui_dict, components
                )

        for agent in self.web_sprite.AVAILABLE_AGENTS:
            creator(agent)

    def create_vanillallm_agent_settings(self, name, feature_class):
        components: Dict[str, Any] = {}
        components["feature_name"] = gr.State(name)

        with gr.Accordion(label="Past Chats", open=False):
            components["chat_tab_history_dropdown"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(OpenAILLM),
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
                value=GradioHelper.dropdown_default_value(OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="Prompts",
                container=True,
            )
            components["chat_tab_prompts_button"] = gr.Button(
                "Load Template", variant="primary", size="sm"
            )
        with gr.Accordion(label="LLM Settings"):
            components["chat_llm_provider"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(LLMService),
                choices=GradioHelper.dropdown_choices(LLMService),
                label="LLM Provider",
                container=True,
            )
            components["chat_llm_model"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="LLM Model",
                container=True,
            )
            with gr.Accordion(label="Advanced Settings", open=False):
                components["chat_llm_advanced"] = gr.Dropdown(
                    value=GradioHelper.dropdown_default_value(OpenAILLM),
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

    def create_ceq_agent_settings(self, name, feature_class):
        components: Dict[str, Any] = {}
        components["feature_name"] = gr.State(name)

        with gr.Accordion(label="Past Chats", open=False):
            components["chat_tab_history_dropdown"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(OpenAILLM),
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
                value=GradioHelper.dropdown_default_value(OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="Prompts",
                container=True,
            )
            components["chat_tab_prompts_button"] = gr.Button(
                "Load Template", variant="primary", size="sm"
            )
        with gr.Accordion(label="LLM Settings"):
            components["chat_llm_provider"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(LLMService),
                choices=GradioHelper.dropdown_choices(LLMService),
                label="LLM Provider",
                container=True,
            )
            components["chat_llm_model"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="LLM Model",
                container=True,
            )
        with gr.Accordion(label="Advanced Settings", open=False):
            components["chat_llm_advanced"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(OpenAILLM),
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

    def create_web_agent_settings(self, name, feature_class):
        components: Dict[str, Any] = {}
        components["feature_name"] = gr.State(name)

        with gr.Accordion(label="Past Chats", open=False):
            components["chat_tab_history_dropdown"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(OpenAILLM),
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
                value=GradioHelper.dropdown_default_value(OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="Prompts",
                container=True,
            )
            components["chat_tab_prompts_button"] = gr.Button(
                "Load Template", variant="primary", size="sm"
            )
        with gr.Accordion(label="LLM Settings"):
            components["chat_llm_provider"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(LLMService),
                choices=GradioHelper.dropdown_choices(LLMService),
                label="LLM Provider",
                container=True,
            )
            components["chat_llm_model"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="LLM Model",
                container=True,
            )
        with gr.Accordion(label="Advanced Settings", open=False):
            components["chat_llm_advanced"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(OpenAILLM),
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
