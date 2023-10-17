import types
from typing import Any, Dict, Generator, List, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.module_base import ModuleBase
from pydantic import BaseModel
from services.llm.llm_openai import OpenAILLM


class LLMService(ModuleBase):
    MODULE_NAME: str = "llm_service"
    MODULE_UI_NAME: str = "LLM Settings"
    PROVIDERS_TYPE: str = "llm_providers"
    REQUIRED_MODULES: List[Type] = [OpenAILLM]

    class ModuleConfigModel(BaseModel):
        llm_provider: str = "openai_llm"

        class Config:
            extra = "ignore"

    config: ModuleConfigModel
    llm_providers: List[Any]

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

    def create_chat(
        self,
        query=None,
        prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
        logit_bias=None,
        max_tokens=None,
        stream=None,
    ):
        if llm_provider is None:
            llm_provider = self.config.llm_provider

        provider_instance = self.get_requested_module_instance(self.llm_providers, llm_provider)
        if provider_instance:
            response = {}
            for response in provider_instance.create_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                documents=documents,
                llm_model=llm_model,
                logit_bias=logit_bias,
                max_tokens=max_tokens,
                stream=stream,
            ):
                yield response

            return {
                "response_content_string": response["response_content_string"],
                "total_prompt_tokens": f"Request token count: {response['total_prompt_tokens']}",
                "total_completion_tokens": f"Response token count: {response['total_completion_tokens']}",
                "total_token_count": f"Total token count: {response['total_token_count']}",
                "model_name": response["model_name"],
            }

    def create_settings_ui(self):
        components = {}

        components["llm_provider"] = gr.Dropdown(
            value=GradioHelper.get_module_ui_name_from_str(self.llm_providers, self.config.llm_provider),
            choices=GradioHelper.get_list_of_module_ui_names(self.llm_providers),
            label="LLM Provider",
            container=True,
        )

        for provider_instance in self.llm_providers:
            provider_instance.create_settings_ui()

        GradioHelper.create_settings_event_listener(self.config, components)

        return components
