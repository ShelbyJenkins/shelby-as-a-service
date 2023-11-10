import types
import typing
from abc import ABC, abstractmethod
from typing import Annotated, Any, Dict, Generator, Optional, Type

import interfaces.webui.gradio_helpers as GradioHelpers
from pydantic import BaseModel, Field
from services.service_base import ServiceBase

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class LLMService(ABC, ServiceBase):
    CLASS_NAME: str = "llm_service"
    CLASS_UI_NAME: str = "LLM Settings"
    AVAILABLE_PROVIDERS: list[Type] = AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    @classmethod
    def load_service_from_provider_name(
        cls,
        llm_provider_name: AVAILABLE_PROVIDERS_NAMES,
        llm_provider_config: dict[str, Any] = {},
        **kwargs,
    ) -> "LLMService":
        return cls.get_requested_class_instance(
            requested_class_name=llm_provider_name,
            requested_class_config=llm_provider_config,
            **kwargs,
        )

    def create_chat(
        self,
        query=None,
        llm_model_name=None,
        logit_bias=None,
        max_tokens=None,
        stream=None,
    ):
        response = {}
        for response in self.create_chat_with_provider(
            query=query,
            llm_model_name=llm_model_name,
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
        llm_model_name=None,
    ) -> tuple[int, int]:
        provider_instance = self.get_requested_class_instance(
            llm_provider if llm_provider is not None else self.config.llm_provider,
        )

        if provider_instance:
            _, llm_model, total_prompt_tokens = provider_instance.prep_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                llm_model_name=llm_model_name,
            )
            available_tokens = llm_model.TOKENS_MAX - 10  # for safety in case of model changes
            available_tokens = available_tokens * (
                model_token_utilization
                if model_token_utilization is not None
                else self.config.model_token_utilization
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

    @abstractmethod
    def create_chat_with_provider(
        self,
        query=None,
        documents=None,
        llm_model_name=None,
        logit_bias=None,
        max_tokens=None,
        stream=None,
    ):
        raise NotImplementedError

    # @classmethod
    # def create_settings_ui(cls):
    #     components = {}

    #     components["model_token_utilization"] = gr.Slider(
    #         value=cls.config.model_token_utilization,
    #         label="Percent of Model Context Size to Use",
    #         minimum=0.0,
    #         maximum=1.0,
    #         step=0.05,
    #         min_width=0,
    #     )

    #     components["llm_provider"] = gr.Dropdown(
    #         value=cls.current_llm_provider.CLASS_UI_NAME,
    #         choices=cls.list_of_class_ui_names,
    #         label="LLM Provider",
    #         container=True,
    #     )

    #     for provider_instance in cls.list_of_required_class_instances:
    #         provider_instance.create_settings_ui()

    #     GradioHelpers.create_settings_event_listener(cls.config, components)

    #     return components
