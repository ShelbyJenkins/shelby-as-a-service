import typing
from typing import Annotated, Any, Dict, Generator, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app.module_base import ModuleBase
from pydantic import BaseModel, Field
from services.llm.llm_service import LLMService


class VanillaLLM(ModuleBase):
    CLASS_NAME: str = "vanillallm_agent"
    CLASS_UI_NAME = "VanillaLLM Agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "agents/vanillallm/vanillallm_prompt_templates.yaml"
    REQUIRED_CLASSES: list[Type] = [LLMService]

    class ClassConfigModel(BaseModel):
        agent_select_status_message: str = "EZPZ"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    llm_service: LLMService
    list_of_required_class_instances: list

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(
            config_file_dict=config_file_dict, llm_provider="openai_llm", model="gpt-4", **kwargs
        )

    def run_chat(
        self,
        chat_in: str,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        model_token_utilization: Optional[float] = None,
        stream: Optional[bool] = None,
        sprite_name: Optional[str] = "webui_sprite",
    ):
        _, max_tokens = self.llm_service.get_available_request_tokens(
            query=chat_in,
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
            model_token_utilization=model_token_utilization,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

        for response in self.llm_service.create_chat(
            query=chat_in,
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
            max_tokens=max_tokens,
        ):
            yield response["response_content_string"]

    def create_settings_ui(self):
        components = {}

        for class_instance in self.list_of_required_class_instances:
            with gr.Tab(label=class_instance.CLASS_UI_NAME):
                class_instance.create_settings_ui()

        GradioHelper.create_settings_event_listener(self.config, components)
