from typing import Any, Dict, List, Optional, Type

import gradio as gr
import sprites.webui.gradio_helpers as GradioHelper
from pydantic import BaseModel
from services.providers.llm_openai import OpenAILLM
from services.service_base import ServiceBase


class LLMService(ServiceBase):
    SERVICE_NAME: str = "llm_service"
    SERVICE_UI_NAME: str = "llm_service"
    PROVIDER_TYPE: str = "llm_provider"
    DEFAULT_PROVIDER: Type = OpenAILLM
    AVAILABLE_PROVIDERS: List[Type] = [OpenAILLM]

    openai_llm: OpenAILLM

    class ServiceConfigModel(BaseModel):
        llm_provider: str = "openai_llm"
        max_response_tokens: int = 300

        class Config:
            extra = "ignore"

    config: ServiceConfigModel

    def __init__(
        self,
        config_dict_from_file: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self.config_dict_from_file = config_dict_from_file or {}
        self.config = self.ServiceConfigModel(**{**kwargs, **self.config_dict_from_file})
        self.provider_config_dict_from_file = self.config_dict_from_file.get("providers", {})
        super().__init__()
        self.config_dict_from_file.update(self.config.model_dump())

        kwargs.pop("llm_provider", None)

        match self.config.llm_provider:
            case "openai_llm":
                self.openai_llm = OpenAILLM(
                    self.provider_config_dict_from_file.get("openai_llm", {}), **kwargs
                )

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

    def create_ui(self):
        components = {}
        llm_providers = ServiceBase.get_provider_instances(self)

        with gr.Column():
            with gr.Accordion(label="LLM Settings", open=False):
                components["llm_provider"] = gr.Dropdown(
                    value=self.config.llm_provider,
                    choices=GradioHelper.dropdown_choices(LLMService),
                    label="LLM Provider",
                    container=True,
                )
                for provider_instance in llm_providers:
                    provider_instance.create_ui()

        return components
