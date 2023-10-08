from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.webui.gradio_helpers as GradioHelper
from services.llm_service import LLMService, OpenAILLM


class UISettings:
    def __init__(self, webui_sprite) -> None:
        self.webui_sprite = webui_sprite
        self.gradio_agents = self.webui_sprite.gradio_ui["gradio_agents"]

    def create_settings_panel(self):
        def creator(agent):
            name = GradioHelper.get_class_name(agent)
            class_instance = getattr(self.webui_sprite, name, None)
            ui_name = GradioHelper.get_class_ui_name(agent)
            existing_ui_dict = self.gradio_agents[name].get("ui", {})
            if ui_name == self.webui_sprite.config.current_agent_ui_name:
                focus = True
            else:
                focus = False
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

                self.gradio_agents[name][
                    "settings_tab_component"
                ] = settings_tab_component

                components_state = {k: gr.State(None) for k in components.keys()}
                self.create_settings_event_listener(components, components_state)

                self.gradio_agents[name][
                    "ui"
                ] = GradioHelper.merge_feature_components_and_create_state(
                    existing_ui_dict, components
                )

        for agent in self.webui_sprite.AVAILABLE_AGENTS:
            creator(agent)

    def create_vanillallm_agent_settings(self, name, agent_instance):
        components: Dict[str, Any] = {}
        components["agent_name"] = gr.State(name)

        with gr.Accordion(label="Past Chats", open=False):
            components["chat_tab_history_dropdown"] = gr.Dropdown(
                value=None,
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
                value=None,
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="Prompts",
                container=True,
            )
            components["chat_tab_prompts_button"] = gr.Button(
                "Load Template", variant="primary", size="sm"
            )
        with gr.Accordion(label="LLM Settings"):
            components["llm_provider"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(agent_instance, LLMService),
                choices=GradioHelper.dropdown_choices(LLMService),
                label="LLM Provider",
                container=True,
            )
            components["llm_model"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(agent_instance, OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="LLM Model",
                container=True,
                elem_classes="llm_model",
            )
            with gr.Accordion(label="Advanced Settings", open=False):
                components["chat_llm_advanced"] = gr.Dropdown(
                    value=None,
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

    def create_ceq_agent_settings(self, name, agent_instance):
        components: Dict[str, Any] = {}
        components["agent_name"] = gr.State(name)

        with gr.Accordion(label="Past Chats", open=False):
            components["chat_tab_history_dropdown"] = gr.Dropdown(
                value=None,
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
                value=None,
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="Prompts",
                container=True,
            )
            components["chat_tab_prompts_button"] = gr.Button(
                "Load Template", variant="primary", size="sm"
            )
        with gr.Accordion(label="LLM Settings"):
            components["llm_provider"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(agent_instance, LLMService),
                choices=GradioHelper.dropdown_choices(LLMService),
                label="LLM Provider",
                container=True,
            )
            components["llm_model"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(agent_instance, OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="LLM Model",
                container=True,
            )
        with gr.Accordion(label="Advanced Settings", open=False):
            components["chat_llm_advanced"] = gr.Dropdown(
                value=None,
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

    def create_web_agent_settings(self, name, agent_instance):
        components: Dict[str, Any] = {}
        components["agent_name"] = gr.State(name)

        with gr.Accordion(label="Past Chats", open=False):
            components["chat_tab_history_dropdown"] = gr.Dropdown(
                value=None,
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
                value=None,
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="Prompts",
                container=True,
            )
            components["chat_tab_prompts_button"] = gr.Button(
                "Load Template", variant="primary", size="sm"
            )
        with gr.Accordion(label="LLM Settings"):
            components["llm_provider"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(agent_instance, LLMService),
                choices=GradioHelper.dropdown_choices(LLMService),
                label="LLM Provider",
                container=True,
            )
            components["llm_model"] = gr.Dropdown(
                value=GradioHelper.dropdown_default_value(agent_instance, OpenAILLM),
                choices=GradioHelper.dropdown_choices(OpenAILLM),
                label="LLM Model",
                container=True,
            )
        with gr.Accordion(label="Advanced Settings", open=False):
            components["chat_llm_advanced"] = gr.Dropdown(
                value=None,
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

    def create_settings_event_listener(self, components, components_state):
        components_to_monitor = []
        for _, component in components.items():
            if isinstance(component, gr.State) or isinstance(component, gr.Button):
                continue
            else:
                components_to_monitor.append(component.change)

        gr.on(
            triggers=components_to_monitor,
            fn=lambda *comp_vals: comp_vals,
            inputs=list(components.values()),
            outputs=list(components_state.values()),
        ).then(
            fn=self.update_config_classes,
            inputs=list(components_state.values()),
        )

    def update_config_classes(self, *components_state):
        ui_state = GradioHelper.comp_values_to_dict(
            self.webui_sprite.gradio_ui, *components_state
        )

        agent = self.webui_sprite.get_selected_agent(ui_state["agent_name"])
        for setting_name, component_setting in ui_state.items():
            if getattr(agent.config, setting_name, None):
                setattr(agent.config, setting_name, component_setting)

        self.webui_sprite.gradio_ui["ui_shared"]["update_settings_file"] = True
