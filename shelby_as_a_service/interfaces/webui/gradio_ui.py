import asyncio
import threading
from decimal import Decimal
from typing import Any, Dict, List, Optional

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.app_base import AppBase
from interfaces.webui.gradio_themes import AtYourServiceTheme


class GradioUI:
    gradio_ui: Dict
    update_settings_file = False
    settings_panel_col_scaling = 2
    chat_ui_panel_col_scaling = 8

    def __init__(self, webui_sprite):
        self.webui_sprite = webui_sprite
        self.required_module_instances = webui_sprite.required_module_instances

        self.available_agents_ui_names = []
        for agent in self.required_module_instances:
            self.available_agents_ui_names.append(agent.MODULE_UI.MODULE_UI_NAME)

        self.gradio_ui = {}
        self.gradio_ui["gradio_agents"] = {}
        self.gradio_agents = self.gradio_ui["gradio_agents"]

    def comp_values_to_dict(self, *values) -> Dict[str, Any]:
        agent_name = values[-1]
        ui_type = values[-2]
        comps_keys = self.gradio_ui["gradio_agents"][agent_name][ui_type]["components"].keys()
        return {k: v for k, v in zip(comps_keys, values)}

    def create_gradio_interface(self):
        all_nav_tabs = []
        all_chat_ui_rows = []

        with gr.Blocks(
            theme=AtYourServiceTheme(),
            css=AtYourServiceTheme.css,
        ) as webui_client:
            with gr.Row(elem_id="main_row"):
                with gr.Column(
                    elem_id="settings_panel_col", scale=self.settings_panel_col_scaling
                ) as settings_panel_col:
                    for agent_instance in self.required_module_instances:
                        all_nav_tabs.append(self.settings_ui_creator(agent_instance))

                with gr.Column(
                    elem_id="chat_ui_panel_col", scale=self.chat_ui_panel_col_scaling
                ) as chat_ui_panel_col:
                    for agent_instance in self.required_module_instances:
                        all_chat_ui_rows.append(self.chat_ui_creator(agent_instance))

            self.create_nav_events(
                all_nav_tabs, all_chat_ui_rows, settings_panel_col, chat_ui_panel_col
            )
            webui_client.load(
                fn=lambda: self.set_agent_view(
                    requested_agent_view=self.webui_sprite.config.current_agent_ui_name
                ),
                outputs=all_chat_ui_rows + [settings_panel_col, chat_ui_panel_col],
            )

            threading.Thread(target=asyncio.run, args=(self.check_for_updates(),)).start()

            webui_client.queue()
            # webui_client.launch(prevent_thread_lock=True)
            webui_client.launch()

    def chat_ui_creator(self, agent_instance):
        agent_name = agent_instance.MODULE_NAME
        agent_ui_class = agent_instance.MODULE_UI

        components = {}

        with gr.Row(
            elem_classes="chat_ui_row",
            elem_id=f"{agent_name}_chat_ui_row",
            visible=False,
        ) as chat_ui_row:
            components = agent_ui_class.create_chat_ui(agent_instance)

        return chat_ui_row

    @staticmethod
    def settings_ui_creator(agent_instance):
        agent_name = agent_instance.MODULE_NAME
        agent_ui_class = agent_instance.MODULE_UI
        agent_ui_name = agent_ui_class.MODULE_UI_NAME

        components = {}

        with gr.Tab(
            label=agent_ui_name,
            elem_id=f"{agent_name}_settings_ui_tab",
        ) as agent_nav_tab:
            agent_ui_class.create_settings_ui(agent_instance)

        return agent_nav_tab

    @staticmethod
    def create_settings_event_listener(class_instance, components):
        def update_config_classes(*values):
            ui_state = {k: v for k, v in zip(components.keys(), values)}
            current_values = class_instance.config.model_dump()
            current_values.update(ui_state)
            class_instance.config = class_instance.ModuleConfigModel(**current_values)
            GradioUI.update_settings_file = True

        components_to_monitor = []
        for _, component in components.items():
            if isinstance(component, gr.State) or isinstance(component, gr.Button):
                continue
            else:
                components_to_monitor.append(component)

        for component in components_to_monitor:
            component.change(
                fn=update_config_classes,
                inputs=components_to_monitor,
            )

    def create_nav_events(
        self, all_nav_tabs, all_chat_ui_rows, settings_panel_col, chat_ui_panel_col
    ):
        outputs = []
        outputs += all_chat_ui_rows
        outputs.append(settings_panel_col)
        outputs.append(chat_ui_panel_col)

        for agent_nav_tab in all_nav_tabs:
            agent_nav_tab.select(
                fn=self.set_agent_view,
                inputs=None,
                outputs=outputs,
            )

    def set_agent_view(
        self, evt: Optional[gr.SelectData] = None, requested_agent_view: Optional[str] = None
    ):
        output = []
        settings_ui_scale = 1
        chat_ui_scale = 1
        if evt and requested_agent_view:
            gr.Error("set_agent_view requires only one of evt or requested_agent_view")
            return
        if requested_agent_view:
            new_agent_view = requested_agent_view
        elif evt:
            new_agent_view = evt.value
        else:
            new_agent_view = self.webui_sprite.config.current_agent_ui_name

        for agent_instance in self.required_module_instances:
            if new_agent_view == agent_instance.MODULE_UI_NAME:
                output.append(gr.Row(visible=True))
                self.webui_sprite.config.current_agent_ui_name = agent_instance.MODULE_UI_NAME
                settings_ui_scale = agent_instance.MODULE_UI.SETTINGS_PANEL_COL
                chat_ui_scale = agent_instance.MODULE_UI.CHAT_UI_PANEL_COL
            else:
                output.append(gr.Row(visible=False))

        output.append(gr.Column(scale=settings_ui_scale))
        output.append(gr.Column(scale=chat_ui_scale))
        GradioUI.update_settings_file = True
        return output

    async def check_for_updates(self):
        while True:
            await asyncio.sleep(5)  # non-blocking sleep
            if GradioUI.update_settings_file:
                GradioUI.update_settings_file = False
                AppBase.update_config_file_from_loaded_models()
