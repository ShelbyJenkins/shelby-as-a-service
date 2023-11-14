from __future__ import annotations

import asyncio
import threading
from typing import Any, Optional, Type

import gradio as gr
import services.gradio_interface.views as views
from app.config_manager import ConfigManager
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase, GradioLogCaptureHandler
from services.gradio_interface.gradio_themes import AtYourServiceTheme


class GradioService(GradioBase):
    CLASS_NAME: str = "gradio_ui"
    CLASS_UI_NAME: str = "gradio_ui"
    REQUIRED_CLASSES: list[Type] = views.AVAILABLE_VIEWS
    AVAILABLE_VIEWS_TYPINGS = views.AVAILABLE_VIEWS_TYPINGS
    AVAILABLE_VIEWS_UI_NAMES: list[str] = views.AVAILABLE_VIEWS_UI_NAMES
    SETTINGS_UI_COL = 2
    PRIMARY_UI_COL = 8

    class ClassConfigModel(BaseModel):
        current_ui_view_name: str = "Chat"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_view_instances: list[views.MainChatView | views.SettingsView | views.DocIndexView] = []
    main_chat_view: "views.MainChatView"
    settings_view: "views.SettingsView"
    doc_index_view: "views.DocIndexView"

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        ConfigManager.add_extension_views_to_gradio_ui(self, self.list_of_extension_configs)
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.list_of_view_instances = self.list_of_required_class_instances

    def create_gradio_interface(self):
        all_setting_ui_tabs = []
        all_primary_ui_rows = []

        with gr.Blocks(
            theme=AtYourServiceTheme(),
            css=AtYourServiceTheme.css,
        ) as webui_client:
            with gr.Row(elem_id="main_row"):
                with gr.Column(
                    elem_id="settings_ui_col", scale=self.SETTINGS_UI_COL
                ) as settings_ui_col:
                    with gr.Tabs(selected=self.config.current_ui_view_name):
                        for view_class in self.list_of_view_instances:
                            all_setting_ui_tabs.append(self.settings_ui_creator(view_class))

                with gr.Column(
                    elem_id="primary_ui_col", scale=self.PRIMARY_UI_COL
                ) as primary_ui_col:
                    for view_class in self.list_of_view_instances:
                        all_primary_ui_rows.append(self.primary_ui_creator(view_class))

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
    def primary_ui_creator(view):
        view_name = view.CLASS_NAME

        with gr.Row(
            elem_classes="primary_ui_row",
            elem_id=f"{view_name}_primary_ui_row",
            visible=False,
        ) as primary_ui_row:
            view.create_primary_ui()

        return primary_ui_row

    @staticmethod
    def settings_ui_creator(view):
        agent_name = view.CLASS_NAME
        agent_ui_name = view.CLASS_UI_NAME

        with gr.Tab(
            id=agent_ui_name,
            label=agent_ui_name,
            elem_id=f"{agent_name}_settings_ui_tab",
        ) as agent_nav_tab:
            view.create_settings_ui()

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

        for view_instance in self.list_of_view_instances:
            if requested_view == view_instance.CLASS_UI_NAME:
                output.append(gr.Row(visible=True))
                self.config.current_ui_view_name = view_instance.CLASS_UI_NAME
                settings_ui_scale = view_instance.SETTINGS_UI_COL
                primary_ui_scale = view_instance.PRIMARY_UI_COL
            else:
                output.append(gr.Row(visible=False))

        output.append(gr.Column(scale=settings_ui_scale))
        output.append(gr.Column(scale=primary_ui_scale))
        self.update_settings_file = True
        return output
