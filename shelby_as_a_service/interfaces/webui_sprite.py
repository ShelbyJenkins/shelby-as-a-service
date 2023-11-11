import typing
from typing import Any, Literal, Optional, Type, get_args

import gradio as gr
from pydantic import BaseModel
from services.gradio_interface.gradio_service import GradioService
from services.service_base import ServiceBase


class WebUISprite(ServiceBase):
    class_name = Literal["webui_sprite"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    CLASS_UI_NAME: str = "webui_sprite"
    REQUIRED_CLASSES: list[Type] = [GradioService]

    class ClassConfigModel(BaseModel):
        default_local_app_enabled: bool = False
        default_local_app_name: Optional[str] = None

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    gradio_ui: GradioService

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def _log(self, message):
        self.log.info(message)
        gr.Info(message)

    def run_sprite(self):
        self.gradio_ui.create_gradio_interface()
