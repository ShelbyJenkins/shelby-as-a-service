from __future__ import annotations

import asyncio
import threading
from typing import Any, Literal, Optional, Type, get_args

from app.config_manager import ConfigManager
from services.gradio_interface.gradio_base import GradioBase


class ExtensionsView(GradioBase):
    class_name = Literal["extensions_view"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Extensions"

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        ConfigManager.add_extension_views_to_gradio_ui(self, self.list_of_extension_configs)
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        # self.list_of_class_instances = self.list_of_required_class_instances

    def create_view_ui(self):
        # for view in self.list_of_class_instances:
        #     with gr.Tab(
        #         id=view.CLASS_NAME,
        #         label=view.CLASS_UI_NAME,
        #         elem_id=f"{view.CLASS_NAME}_settings_ui_tab",
        #     ) as agent_nav_tab:
        #     view.create_view_ui()
        pass

    @property
    def view_css(self) -> str:
        return ""
