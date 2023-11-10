import asyncio
import threading
import typing
from decimal import Decimal
from typing import Any, Optional, Type

import gradio as gr
from app.config_manager import ConfigManager
from interfaces.webui.gradio_themes import AtYourServiceTheme
from interfaces.webui.views.context_index_view import ContextIndexView
from interfaces.webui.views.main_chat_view import MainChatView
from interfaces.webui.views.settings_view import SettingsView
from pydantic import BaseModel
from services.service_base import ServiceBase


class GradioUI(ServiceBase):
    CLASS_NAME: str = "gradio_ui"
    CLASS_UI_NAME: str = "gradio_ui"
    settings_ui_col_scaling = 2
    primary_ui_col_scaling = 8

    # REQUIRED_CLASSES: list[Type] = [MainChatView, ContextIndexView, SettingsView]
    REQUIRED_CLASSES: list[Type] = [MainChatView, ContextIndexView]
    # REQUIRED_CLASSES: list[Type] = [MainChatView]

    class ClassConfigModel(BaseModel):
        current_ui_view_name: str = "Chat"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    webui_sprite: Any
    list_of_class_names: list
    list_of_class_ui_names: list
    list_of_required_class_instances: list
    list_of_extension_configs: Optional[list]

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        ConfigManager.add_extension_views_to_gradio_ui(self, self.list_of_extension_configs)
        super().__init__(config=config, **kwargs)

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
                    with gr.Tabs(selected=self.config.current_ui_view_name):
                        for view_instance in self.list_of_required_class_instances:
                            all_setting_ui_tabs.append(self.settings_ui_creator(view_instance))

                with gr.Column(
                    elem_id="primary_ui_col", scale=self.primary_ui_col_scaling
                ) as primary_ui_col:
                    for view_instance in self.list_of_required_class_instances:
                        all_primary_ui_rows.append(self.primary_ui_creator(view_instance))

            self.create_nav_events(
                all_setting_ui_tabs, all_primary_ui_rows, settings_ui_col, primary_ui_col
            )

            webui_client.load(
                fn=lambda: self.set_agent_view(requested_view=self.config.current_ui_view_name),
                outputs=all_primary_ui_rows + [settings_ui_col, primary_ui_col],
            )

            threading.Thread(target=asyncio.run, args=(self.check_for_updates(),)).start()

            webui_client.queue()
            # webui_client.launch(prevent_thread_lock=True, show_error=True)
            try:
                webui_client.launch(show_error=True)
            except Warning as w:
                self.log.warning(w)
                gr.Warning(message=str(w))

    @staticmethod
    def primary_ui_creator(view_instance):
        view_name = view_instance.CLASS_NAME

        with gr.Row(
            elem_classes="primary_ui_row",
            elem_id=f"{view_name}_primary_ui_row",
            visible=False,
        ) as primary_ui_row:
            view_instance.create_primary_ui()

        return primary_ui_row

    @staticmethod
    def settings_ui_creator(view_instance):
        agent_name = view_instance.CLASS_NAME
        agent_ui_name = view_instance.CLASS_UI_NAME

        with gr.Tab(
            id=agent_ui_name,
            label=agent_ui_name,
            elem_id=f"{agent_name}_settings_ui_tab",
        ) as agent_nav_tab:
            view_instance.create_settings_ui()

        return agent_nav_tab

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

        for view_instance in self.list_of_required_class_instances:
            if requested_view == view_instance.CLASS_UI_NAME:
                output.append(gr.Row(visible=True))
                self.config.current_ui_view_name = view_instance.CLASS_UI_NAME
                settings_ui_scale = view_instance.SETTINGS_UI_COL
                primary_ui_scale = view_instance.PRIMARY_UI_COL
            else:
                output.append(gr.Row(visible=False))

        output.append(gr.Column(scale=settings_ui_scale))
        output.append(gr.Column(scale=primary_ui_scale))
        ModuleBase.update_settings_file = True
        return output

    async def check_for_updates(self):
        while True:
            await asyncio.sleep(5)  # non-blocking sleep
            if ModuleBase.update_settings_file:
                ModuleBase.update_settings_file = False
                ConfigManager.update_config_file_from_loaded_models()
