import typing
from typing import Any, Dict, Generator, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from interfaces.webui.gradio_ui import GradioUI
from pydantic import BaseModel


class WebUISprite(ModuleBase):
    CLASS_NAME: str = "webui_sprite"
    CLASS_UI_NAME: str = "webui_sprite"
    REQUIRED_CLASSES: list[Type] = [GradioUI]

    class ClassConfigModel(BaseModel):
        default_local_app_enabled: bool = False
        default_local_app_name: Optional[str] = None

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    gradio_ui: GradioUI

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        GradioUI.webui_sprite = self
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def _log(self, message):
        self.log.info(message)
        gr.Info(message)

    def run_sprite(self):
        self.gradio_ui.create_gradio_interface()
