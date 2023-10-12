from decimal import Decimal
from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.webui.gradio_helpers as GradioHelper
from sprites.webui.gradio_themes import AtYourServiceTheme


class GradioUI:
    def __init__(self, webui_sprite):
        self.webui_sprite = webui_sprite
        self.available_agent_instances = webui_sprite.available_agent_instances

        self.available_agents_ui_names = []
        for agent in self.webui_sprite.AVAILABLE_AGENTS:
            ui_name = GradioHelper.get_class_ui_name(agent)
            self.available_agents_ui_names.append(ui_name)
            if ui_name == self.available_agents_ui_names[0]:
                self.settings_panel_col_scaling = agent.AGENT_UI.SETTINGS_PANEL_COL
                self.chat_ui_panel_col_scaling = agent.AGENT_UI.CHAT_UI_PANEL_COL

        self.gradio_ui = {}
        self.gradio_ui["update_settings_file"] = gr.State(False)
        self.gradio_ui["gradio_agents"] = {}
        self.gradio_agents = self.gradio_ui["gradio_agents"]

    def create_gradio_interface(self):
        with gr.Blocks(
            theme=AtYourServiceTheme(),
            css=AtYourServiceTheme.css,
        ) as webui_client:
            with gr.Row(elem_id="main_row"):
                with gr.Column(
                    elem_id="settings_panel_col", scale=self.settings_panel_col_scaling
                ) as settings_panel_col:
                    for agent_instance in self.available_agent_instances:
                        self.settings_ui_creator(agent_instance)

                with gr.Column(
                    elem_id="chat_ui_panel_col", scale=self.chat_ui_panel_col_scaling
                ) as chat_ui_panel_col:
                    for agent_instance in self.available_agent_instances:
                        self.chat_ui_creator(agent_instance)

            # self.gradio_ui["settings_panel_col"] = settings_panel_col
            # self.gradio_ui["chat_ui_panel_col"] = chat_ui_panel_col

            # for agent_instance in self.available_agent_instances:
            #     self.create_event_handlers(agent_instance)

            # self.create_nav_events()
            webui_client.queue()
            # webui_client.launch(prevent_thread_lock=True)
            webui_client.launch()

    def chat_ui_creator(self, agent_instance):
        agent_name = GradioHelper.get_class_name(agent_instance)
        ui_name = GradioHelper.get_class_ui_name(agent_instance)

        self.gradio_agents.setdefault(agent_name, {})
        gradio_agent = self.gradio_agents[agent_name]

        if ui_name == self.available_agents_ui_names[0]:
            gradio_agent["visibility"] = True
        else:
            gradio_agent["visibility"] = False

        with gr.Row(
            elem_classes="chat_ui_row",
            elem_id=f"{agent_name}_chat_ui_row",
            visible=gradio_agent["visibility"],
        ) as gradio_agent["chat_ui_row"]:
            components = agent_instance.AGENT_UI().create_chat_ui(agent_instance)

            components["ui_type"] = gr.State("chat_ui")
            components["agent_name"] = gr.State(agent_name)

            gradio_agent["chat_ui"] = {}
            gradio_agent["chat_ui"]["components"] = components
            components_state = {k: gr.State(None) for k in components.keys()}
            gradio_agent["chat_ui"]["components_state"] = components_state

    def settings_ui_creator(self, agent_instance):
        agent_name = agent_instance.AGENT_NAME
        agent_ui_class = agent_instance.AGENT_UI
        agent_ui_name = agent_ui_class.AGENT_UI_NAME

        components = {}

        with gr.Tab(
            label=agent_ui_name,  # type: ignore
            elem_id=f"{agent_name}_settings_ui_tab",
        ) as components["settings_ui_tab"]:
            components = agent_ui_class.create_settings_ui(agent_instance)

            components["ui_type"] = gr.State("settings_ui")
            components["agent_name"] = gr.State(agent_name)

            components["settings_ui"] = {}
            components["settings_ui"]["components"] = components
            components_state = {k: gr.State(None) for k in components.keys()}
            components["settings_ui"]["components_state"] = components_state

            # self.create_settings_event_listener(components, components_state)

        self.gradio_agents.setdefault(agent_name, {})
        self.gradio_agents[agent_name]

    # def create_event_handlers(self, agent_class):
    #     if getattr(agent_class.AGENT_UI, "create_event_handlers", None):
    #         agent_name = GradioHelper.get_class_name(agent_class)
    #         gradio_agent = self.gradio_agents[agent_name]

    #         agent_class.AGENT_UI(self.webui_sprite).create_event_handlers(
    #             gradio_agent["chat_ui"]["components"],
    #             gradio_agent["chat_ui"]["components_state"],
    #         )

    # def create_settings_event_listener(self, components, components_state):
    #     components_to_monitor = []
    #     for _, component in components.items():
    #         if isinstance(component, gr.State) or isinstance(component, gr.Button):
    #             continue
    #         else:
    #             components_to_monitor.append(component.change)

    #     gr.on(
    #         triggers=components_to_monitor,
    #         fn=lambda *comp_vals: comp_vals,
    #         inputs=list(components.values()),
    #         outputs=list(components_state.values()),
    #     ).then(
    #         fn=self.update_config_classes,
    #         inputs=list(components_state.values()),
    #     )

    # def update_config_classes(self, *components_state):
    #     ui_state = GradioHelper.comp_values_to_dict(self.webui_sprite.gradio_ui, *components_state)

    #     agent = self.webui_sprite.get_selected_agent(ui_state["agent_name"])
    #     for setting_name, component_setting in ui_state.items():
    #         if getattr(agent.config, setting_name, None):
    #             setattr(agent.config, setting_name, component_setting)

    #     self.webui_sprite.gradio_ui["update_settings_file"] = True

    # def create_nav_events(self):
    #     all_nav_tabs = []
    #     all_chat_ui_rows = []
    #     for _, agent in self.webui_sprite.gradio_ui["gradio_agents"].items():
    #         all_nav_tabs.append(agent["settings_ui_tab"])
    #         all_chat_ui_rows.append(agent["chat_ui_row"])

    #     all_chat_ui_rows.append(self.gradio_ui["settings_panel_col"])
    #     all_chat_ui_rows.append(self.gradio_ui["chat_ui_panel_col"])

    #     for agent_nav_tab in all_nav_tabs:
    #         agent_nav_tab.select(
    #             fn=self.change_agent,
    #             inputs=None,
    #             outputs=all_chat_ui_rows,
    #         )

    # def change_agent(self, evt: gr.SelectData):
    #     output = []
    #     for agent in self.webui_sprite.AVAILABLE_AGENTS:
    #         ui_name = GradioHelper.get_class_ui_name(agent)
    #         if evt.value == ui_name:
    #             output.append(gr.Row(visible=True))
    #             self.webui_sprite.config.current_agent_ui_name = ui_name
    #             settings_ui_scale = agent.AGENT_UI.SETTINGS_PANEL_COL
    #             chat_ui_scale = agent.AGENT_UI.CHAT_UI_PANEL_COL
    #         else:
    #             output.append(gr.Row(visible=False))

    #     output.append(gr.Column(scale=settings_ui_scale))
    #     output.append(gr.Column(scale=chat_ui_scale))

    #     return output
