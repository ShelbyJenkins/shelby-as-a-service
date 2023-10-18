import types
from typing import Annotated, Any, Dict, Generator, List, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.module_base import ModuleBase
from pydantic import BaseModel, Field
from services.llm.llm_openai import OpenAILLM


class LLMService(ModuleBase):
    MODULE_NAME: str = "llm_service"
    MODULE_UI_NAME: str = "LLM Settings"
    PROVIDERS_TYPE: str = "llm_providers"
    REQUIRED_MODULES: List[Type] = [OpenAILLM]

    class ModuleConfigModel(BaseModel):
        llm_provider: str = "openai_llm"
        model_token_utilization: Annotated[float, Field(ge=0, le=1.0)] = 0.5

        class Config:
            extra = "ignore"

    config: ModuleConfigModel
    llm_providers: List[Any]
    list_of_module_ui_names: list
    current_llm_provider: Any

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)
        self.current_llm_provider = self.get_requested_module_instance(self.llm_providers, self.config.llm_provider)

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
        provider_instance = self.get_requested_module_instance(
            self.llm_providers, llm_provider if llm_provider is not None else self.config.llm_provider
        )
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

    def get_available_request_tokens(
        self,
        query,
        prompt_template_path,
        model_token_utilization=None,
        context_to_response_ratio=0.00,
        llm_provider=None,
        llm_model=None,
    ) -> tuple[int, int]:
        provider_instance = self.get_requested_module_instance(
            self.llm_providers, llm_provider if llm_provider is not None else self.config.llm_provider
        )

        if provider_instance:
            _, llm_model, total_prompt_tokens = provider_instance.prep_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                llm_model=llm_model,
            )
            available_tokens = llm_model.TOKENS_MAX - 10  # for safety in case of model changes
            available_tokens = available_tokens * (
                model_token_utilization if model_token_utilization is not None else self.config.model_token_utilization
            )
            if context_to_response_ratio > 0.0:
                available_request_tokens = available_tokens * context_to_response_ratio
                available_request_tokens = available_request_tokens - total_prompt_tokens
            else:
                available_request_tokens = available_tokens - total_prompt_tokens
            available_response_tokens = available_tokens - available_request_tokens
            max_tokens = available_response_tokens + available_request_tokens

            return int(available_request_tokens), int(max_tokens)
        else:
            return 0, 0

    def create_settings_ui(self):
        components = {}

        components["model_token_utilization"] = gr.Slider(
            value=self.config.model_token_utilization,
            label="Percent of Model Context Size to Use",
            minimum=0.0,
            maximum=1.0,
            step=0.05,
            min_width=0,
        )

        components["llm_provider"] = gr.Dropdown(
            value=self.current_llm_provider.MODULE_UI_NAME,
            choices=self.list_of_module_ui_names,
            label="LLM Provider",
            container=True,
        )

        for provider_instance in self.llm_providers:
            provider_instance.create_settings_ui()

        GradioHelper.create_settings_event_listener(self.config, components)

        return components
