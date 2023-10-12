from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from pydantic import BaseModel
from services.llm.llm_openai import OpenAILLM
from services.service_base import ServiceBase


class LLMService(ServiceBase):
    MODULE_NAME: str = "llm_service"
    MODULE_UI_NAME: str = "llm_service"
    PROVIDER_TYPE: str = "llm_provider"
    DEFAULT_PROVIDER: Type = OpenAILLM
    REQUIRED_MODULES: List[Type] = [OpenAILLM]

    openai_llm: OpenAILLM

    class ServiceConfigModel(BaseModel):
        llm_provider: str = "openai_llm"
        max_response_tokens: int = 300

        class Config:
            extra = "ignore"

    config: ServiceConfigModel

    def __init__(
        self,
        config_file_dict={},
        **kwargs,
    ):
        # super().__init__()
        module_config_file_dict = config_file_dict.get(self.MODULE_NAME, {})
        self.config = self.ServiceConfigModel(**{**kwargs, **module_config_file_dict})

        self.openai_llm = OpenAILLM(module_config_file_dict)

    def create_streaming_chat(
        self,
        query,
        prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ):
        provider = self.get_provider(new_provider_name=llm_provider)
        if provider:
            yield from provider._create_streaming_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                documents=documents,
                llm_model=llm_model,
            )

    def create_chat(
        self,
        query,
        prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ) -> Optional[str]:
        provider = self.get_provider(new_provider_name=llm_provider)
        if provider:
            return provider._create_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                documents=documents,
                llm_model=llm_model,
            )
        return None

    def create_settings_ui(self):
        components = {}
        llm_providers, default_llm_provider = self.get_provider_names(self.config.llm_provider)

        with gr.Column():
            with gr.Accordion(label="LLM Settings", open=False):
                components["llm_provider"] = gr.Dropdown(
                    value=default_llm_provider,
                    choices=llm_providers,
                    label="LLM Provider",
                    container=True,
                )
                for provider_instance in self.available_provider_instances:
                    provider_instance.create_ui()

        return components
