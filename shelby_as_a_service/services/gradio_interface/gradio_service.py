from __future__ import annotations

import asyncio
import threading
from typing import Any, Optional, Type

import gradio as gr
import services.gradio_interface.views as views
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase
from services.gradio_interface.gradio_themes import AtYourServiceTheme


class ClassConfigModel(BaseModel):
    current_ui_view_name: str = "Agora"

    class Config:
        extra = "ignore"


class GradioService(GradioBase):
    CLASS_NAME: str = "gradio_ui"
    CLASS_UI_NAME: str = "gradio_ui"
    REQUIRED_CLASSES: list[Type] = views.AVAILABLE_CLASSES
    AVAILABLE_CLASSES_TYPINGS = views.AVAILABLE_CLASSES_TYPINGS
    AVAILABLE_CLASSES_UI_NAMES: list[str] = views.AVAILABLE_CLASSES_UI_NAMES

    class_config_model = ClassConfigModel
    config: ClassConfigModel
    list_of_class_instances: list[views.AgoraView | views.AdvancedView | views.ExtensionsView]

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.list_of_class_instances = self.list_of_required_class_instances

    def create_gradio_interface(self):
        interface_css = AtYourServiceTheme.css
        for view in self.list_of_class_instances:
            interface_css += view.view_css
        with gr.Blocks(
            theme=AtYourServiceTheme(),
            css=interface_css,
        ) as webui_client:
            with gr.Row(elem_id="primary_ui_row"):
                with gr.Tabs(elem_classes="primary_ui_tabs"):
                    for view in self.list_of_class_instances:
                        with gr.Tab(
                            id=view.CLASS_NAME,
                            label=view.CLASS_UI_NAME,
                            elem_classes="primary_ui_tab",
                        ) as agent_nav_tab:
                            view.create_view_ui()

            # self.create_nav_events(
            #     all_setting_ui_tabs, all_primary_ui_rows, settings_ui_col, primary_ui_col
            # )

            # webui_client.load(
            #     fn=lambda: self.set_agent_view(requested_view=self.config.current_ui_view_name),
            #     outputs=all_primary_ui_rows + [settings_ui_col, primary_ui_col],
            # )

        threading.Thread(target=asyncio.run, args=(self.check_for_updates(),)).start()

        webui_client.queue()
        # webui_client.launch(prevent_thread_lock=True, show_error=True)
        try:
            webui_client.launch(show_error=True, show_api=False)
        except Warning as w:
            self.log.warning(w)
            gr.Warning(message=str(w))

    def create_nav_events(
        self, all_setting_ui_tabs, all_primary_ui_rows, settings_ui_col, primary_ui_col
    ):
        outputs: list = []
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

        for view_instance in self.list_of_class_instances:
            if requested_view == view_instance.CLASS_UI_NAME:
                output.append(gr.Row(visible=True))
                self.config.current_ui_view_name = view_instance.CLASS_UI_NAME
                settings_ui_scale = view_instance.SETTINGS_UI_COL
                primary_ui_scale = view_instance.PRIMARY_UI_COL
            else:
                output.append(gr.Row(visible=False))

        output.append(gr.Column(scale=settings_ui_scale))
        output.append(gr.Column(scale=primary_ui_scale))
        GradioBase.update_settings_file = True
        return output
