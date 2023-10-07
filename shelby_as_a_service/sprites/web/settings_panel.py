from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.web.gradio_helpers as GradioHelper
from services.llm_service import LLMService, OpenAILLM


class SettingsPanel:
    def __init__(self, web_sprite) -> None:
        self.web_sprite = web_sprite
        self.features = self.web_sprite.ui["features"]
        self.available_agents_ui_names: List[str] = []
        self.available_agents_names: List[str] = []
        for agent in web_sprite.AVAILABLE_AGENTS:
            self.available_agents_ui_names.append(GradioHelper.get_class_ui_name(agent))
            self.available_agents_names.append(GradioHelper.get_class_name(agent))

    def create_settings_panel(self):
        def creator(agent):
            name = GradioHelper.get_class_name(agent)
            class_instance = getattr(self.web_sprite, name, None)
            ui_name = GradioHelper.get_class_ui_name(agent)
            with gr.Tab(
                label=ui_name,
                elem_id=f"{name}_settings_tab_component",
            ) as self.features[name]["settings_tab_component"]:
                match name:
                    case "vanillallm_agent":
                        self.features[name][
                            "settings_tab"
                        ] = self.create_vanillallm_agent_settings(class_instance)
                    case "ceq_agent":
                        self.features[name][
                            "settings_tab"
                        ] = self.create_vanillallm_agent_settings(class_instance)
                    case "web_agent":
                        self.features[name][
                            "settings_tab"
                        ] = self.create_vanillallm_agent_settings(class_instance)

        for agent in self.web_sprite.AVAILABLE_AGENTS:
            creator(agent)

    def create_vanillallm_agent_settings(self, feature_class):
        components: Dict[str, Any] = {}
        components_state: Dict[str, Any] = {}

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

        components_state = {k: gr.State(None) for k in components.keys()}

        # self.event_handlers(components, components_state)
        return {
            "components": components,
            "components_state": components_state,
        }

    def create_ceq_agent_settings(self, feature_class):
        components: Dict[str, Any] = {}
        components_state: Dict[str, Any] = {}

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
        components_state = {k: gr.State(None) for k in components.keys()}

        # self.event_handlers(components, components_state)
        return {
            "components": components,
            "components_state": components_state,
        }

    def create_web_agent_settings(self, feature_class):
        components: Dict[str, Any] = {}
        components_state: Dict[str, Any] = {}

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
        components_state = {k: gr.State(None) for k in components.keys()}

        # self.event_handlers(components, components_state)
        return {
            "components": components,
            "components_state": components_state,
        }

    def create_feature_nav_event(self):
        all_nav_tabs = []
        all_chat_ui_rows = []
        for _, feature in self.web_sprite.ui["features"].items():
            all_nav_tabs.append(feature["settings_tab_component"])
            all_chat_ui_rows.append(feature["chat_ui_row"])

        for feature_nav_tab in all_nav_tabs:
            feature_nav_tab.select(
                fn=self.change_feature,
                inputs=None,
                outputs=all_chat_ui_rows,
            )

    def change_feature(self, evt: gr.SelectData):
        output = []
        for ui_name in self.available_agents_ui_names:
            if evt.value == ui_name:
                output.append(gr.Row(visible=True))
                self.web_sprite.config.current_feature_ui_name = ui_name
            else:
                output.append(gr.Row(visible=False))
        return output
