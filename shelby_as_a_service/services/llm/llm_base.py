from abc import ABC, abstractmethod
from typing import Any, Type

import gradio as gr
import services.llm as llm
from pydantic import BaseModel
from services.service_base import ServiceBase


class LLMBase(ABC, ServiceBase):
    ModelConfig: Type[BaseModel]
    config: BaseModel
    MODEL_DEFINITIONS: dict[str, Any]

    def get_model_instance(
        self, requested_model_name: str, llm_provider_instance: "LLMBase"
    ) -> Any:
        for model_name, model in llm_provider_instance.MODEL_DEFINITIONS.items():
            if model_name == requested_model_name:
                model_instance = llm_provider_instance.ModelConfig(**model)
                return model_instance

        raise ValueError(f"Requested model {requested_model_name} not found.")

    def set_current_model(self, requested_model):
        output = []
        for model_name, model in self.config.available_models.items():
            ui_name = model_name
            if ui_name == requested_model:
                self.current_model_class = model
                self.config.enabled_model_name = ui_name
                self.update_settings_file = True
                output.append(gr.Group(visible=True))
            else:
                output.append(gr.Group(visible=False))
        return output

    @abstractmethod
    def create_chat(
        self,
        prompt,
        llm_model_instance,
        logit_bias=None,
        max_tokens=None,
        stream=None,
    ):
        raise NotImplementedError

    def create_settings_ui(self):
        pass
