import asyncio
import threading
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type

import gradio as gr
from app_config.config_manager import ConfigManager
from app_config.module_base import ModuleBase
from interfaces.webui.gradio_themes import AtYourServiceTheme
from interfaces.webui.views.context_index_view import ContextIndexView
from interfaces.webui.views.main_chat_view import MainChatView
from interfaces.webui.views.settings_view import SettingsView


class GradioUI(ModuleBase):
    gradio_ui: Dict
    update_settings_file = False
    settings_ui_col_scaling = 2
    primary_ui_col_scaling = 8
    UI_VIEWS: List[Type] = [MainChatView, ContextIndexView, SettingsView]

    def __init__(self, webui_sprite):
        self.webui_sprite = webui_sprite
        self.ui_view_instances = []
        self.main_chat_view = MainChatView(self.webui_sprite)
        self.ui_view_instances.append(self.main_chat_view)
        self.context_index_view = ContextIndexView(self.webui_sprite)
        self.ui_view_instances.append(self.context_index_view)
        self.settings_view = SettingsView(self.webui_sprite)
        self.ui_view_instances.append(self.settings_view)

        ConfigManager.add_extension_views_to_gradio_ui(
            self, self.webui_sprite, self.list_of_extension_configs
        )

    def create_gradio_interface(self):
        all_setting_ui_tabs = []
        all_primary_ui_rows = []

        with gr.Blocks(
            theme=AtYourServiceTheme(),
            css=AtYourServiceTheme.css,
        ) as webui_client:
            with gr.Row(elem_id="main_row"):
                with gr.Column(
                    elem_id="settings_ui_col", scale=self.settings_ui_col_scaling
                ) as settings_ui_col:
                    for view_instance in self.ui_view_instances:
                        all_setting_ui_tabs.append(self.settings_ui_creator(view_instance))

                with gr.Column(
                    elem_id="primary_ui_col", scale=self.primary_ui_col_scaling
                ) as primary_ui_col:
                    for view_instance in self.ui_view_instances:
                        all_primary_ui_rows.append(self.primary_ui_creator(view_instance))

            self.create_nav_events(
                all_setting_ui_tabs, all_primary_ui_rows, settings_ui_col, primary_ui_col
            )

            webui_client.load(
                fn=lambda: self.set_agent_view(requested_view="Main Chat"),
                outputs=all_primary_ui_rows + [settings_ui_col, primary_ui_col],
            )

            threading.Thread(target=asyncio.run, args=(self.check_for_updates(),)).start()

            webui_client.queue()
            webui_client.launch(prevent_thread_lock=True)
            webui_client.launch()

    def primary_ui_creator(self, view_instance):
        view_name = view_instance.MODULE_NAME

        with gr.Row(
            elem_classes="primary_ui_row",
            elem_id=f"{view_name}_primary_ui_row",
            visible=False,
        ) as primary_ui_row:
            view_instance.create_primary_ui()

        return primary_ui_row

    @staticmethod
    def settings_ui_creator(view_instance):
        agent_name = view_instance.MODULE_NAME
        agent_ui_name = view_instance.MODULE_UI_NAME

        with gr.Tab(
            label=agent_ui_name,
            elem_id=f"{agent_name}_settings_ui_tab",
        ) as agent_nav_tab:
            view_instance.create_settings_ui()

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
        self, all_setting_ui_tabs, all_primary_ui_rows, settings_ui_col, primary_ui_col
    ):
        outputs = []
        outputs += all_primary_ui_rows
        outputs.append(settings_ui_col)
        outputs.append(primary_ui_col)

        for agent_nav_tab in all_setting_ui_tabs:
            agent_nav_tab.select(
                fn=self.get_nav_evt,
                inputs=None,
                outputs=outputs,
            )

    def get_nav_evt(self, evt: gr.SelectData):
        output = self.set_agent_view(evt.value)
        return output

    def set_agent_view(self, requested_view: str):
        output = []
        settings_ui_scale = 1
        primary_ui_scale = 1

        for view_instance in self.ui_view_instances:
            if requested_view == view_instance.MODULE_UI_NAME:
                output.append(gr.Row(visible=True))
                self.webui_sprite.config.current_ui_view_name = view_instance.MODULE_UI_NAME
                settings_ui_scale = view_instance.SETTINGS_UI_COL
                primary_ui_scale = view_instance.PRIMARY_UI_COL
            else:
                output.append(gr.Row(visible=False))

        output.append(gr.Column(scale=settings_ui_scale))
        output.append(gr.Column(scale=primary_ui_scale))
        GradioUI.update_settings_file = True
        return output

    async def check_for_updates(self):
        while True:
            await asyncio.sleep(5)  # non-blocking sleep
            if GradioUI.update_settings_file:
                GradioUI.update_settings_file = False
                ConfigManager.update_config_file_from_loaded_models()
