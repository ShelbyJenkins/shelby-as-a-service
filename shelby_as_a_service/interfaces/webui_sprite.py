import typing
from typing import Any, Optional, Type

import gradio as gr
from pydantic import BaseModel
from services.service_base import ServiceBase

from shelby_as_a_service.services.gradio_interface.gradio_service import GradioService


class WebUISprite(ServiceBase):
    CLASS_NAME: str = "webui_sprite"
    CLASS_UI_NAME: str = "webui_sprite"
    REQUIRED_CLASSES: list[Type] = [GradioService]

    class ClassConfigModel(BaseModel):
        default_local_app_enabled: bool = False
        default_local_app_name: Optional[str] = None

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    gradio_ui: GradioService

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        super().__init__(config=config, **kwargs)

    def _log(self, message):
        self.log.info(message)
        gr.Info(message)

    def run_sprite(self):
        self.gradio_ui.create_gradio_interface()
