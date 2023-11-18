from typing import Any, Generator, Optional, Type

import gradio as gr
import services.llm as llm
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase
from services.llm.llm_base import LLMBase


class ClassConfigModel(BaseModel):
    current_llm_provider_name: str = "openai_llm"
    stream: bool = False

    class Config:
        extra = "ignore"


class LLMService(LLMBase):
    CLASS_NAME: str = "llm_service"
    CLASS_UI_NAME: str = "LLM Settings"
    REQUIRED_CLASSES: list[Type] = llm.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list = llm.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_TYPINGS = llm.AVAILABLE_PROVIDERS_TYPINGS
    class_config_model = ClassConfigModel
    config: ClassConfigModel

    def __init__(
        self,
        llm_provider_name: Optional[llm.AVAILABLE_PROVIDERS_TYPINGS] = None,
        llm_model_name: Optional[str] = None,
        config_file_dict: dict[str, Any] = {},
        **kwargs,
    ):
        if not llm_provider_name:
            llm_provider_name = kwargs.pop("llm_provider_name", None)
        if not llm_provider_name:
            llm_provider_name = ClassConfigModel().current_llm_provider_name  # type: ignore
        else:
            kwargs.pop("llm_provider_name", None)
        if not llm_model_name:
            llm_model_name = kwargs.pop("llm_model_name", None)
        else:
            kwargs.pop("llm_model_name", None)

        super().__init__(
            provider_name=llm_provider_name,
            provider_model_name=llm_model_name,
            config_file_dict=config_file_dict,
            **kwargs,
        )
        if self.list_of_required_class_instances:
            self.list_of_llm_provider_instances = self.list_of_required_class_instances

        if not self.current_provider_instance:
            raise ValueError("current_provider_instance not properly set!")

        self.llm_provider: LLMBase = self.current_provider_instance

    def generate_text(
        self,
        prompt: list[dict[str, str]],
        token_utilization: float = 1,
        max_tokens: Optional[int] = None,
    ):
        total_prompt_tokens, new_max_tokens = self.get_available_request_tokens(
            prompt=prompt,
            token_utilization=token_utilization,
            llm_provider=self.llm_provider,
        )
        if max_tokens is None:
            max_tokens = new_max_tokens

        llm_model_instance = self.llm_provider.llm_model_instance
        # Already set in get_available_request_tokens, but here for safety
        while max_tokens + total_prompt_tokens > (llm_model_instance.TOKENS_MAX - 15):
            max_tokens -= 1

        response = self.llm_provider.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
        )

        total_token_count = self.calculate_cost(
            total_token_count=total_prompt_tokens + response["total_response_tokens"],
            llm_model_instance=llm_model_instance,
        )
        return {
            "response_content_string": response["response_content_string"],
            "total_prompt_tokens": f"Request token count: {total_prompt_tokens}",
            "total_response_tokens": f"Response token count: {response['total_response_tokens']}",
            "total_token_count": f"Total token count: {total_token_count}",
            "model_name": llm_model_instance.MODEL_NAME,
        }

    def make_decision(
        self,
        prompt: list[dict[str, str]],
        logit_bias: dict[str, int],
        max_tokens: int,
    ):
        total_prompt_tokens, _ = self.get_available_request_tokens(
            prompt=prompt,
            token_utilization=1,
            llm_provider=self.llm_provider,
        )

        llm_model_instance = self.llm_provider.llm_model_instance
        # Already set in get_available_request_tokens, but here for safety
        while max_tokens + total_prompt_tokens > (llm_model_instance.TOKENS_MAX - 15):
            max_tokens -= 1

        response = self.llm_provider.make_decision(
            prompt=prompt,
            max_tokens=max_tokens,
            logit_bias=logit_bias,
        )

        total_token_count = self.calculate_cost(
            total_token_count=total_prompt_tokens + response["total_response_tokens"],
            llm_model_instance=llm_model_instance,
        )
        return {
            "response_content_string": response["response_content_string"],
            "total_prompt_tokens": f"Request token count: {total_prompt_tokens}",
            "total_response_tokens": f"Response token count: {response['total_response_tokens']}",
            "total_token_count": f"Total token count: {total_token_count}",
            "model_name": llm_model_instance.MODEL_NAME,
        }

    def create_chat(
        self,
        prompt: list[dict[str, str]],
        token_utilization: float = 0.5,
        stream: Optional[bool] = None,
    ):
        total_prompt_tokens, max_tokens = self.get_available_request_tokens(
            prompt=prompt,
            token_utilization=token_utilization,
            llm_provider=self.llm_provider,
        )

        llm_model_instance = self.llm_provider.llm_model_instance
        # For safety
        while max_tokens + total_prompt_tokens > (llm_model_instance.TOKENS_MAX - 15):
            max_tokens -= 1

        response = {}
        for response in self.llm_provider.create_chat(
            prompt=prompt,
            max_tokens=max_tokens,
            stream=stream if stream is not None else self.config.stream,
        ):
            yield response

        total_token_count = self.calculate_cost(
            total_token_count=total_prompt_tokens + response["total_response_tokens"],
            llm_model_instance=llm_model_instance,
        )
        return {
            "response_content_string": response["response_content_string"],
            "total_prompt_tokens": f"Request token count: {total_prompt_tokens}",
            "total_response_tokens": f"Response token count: {response['total_response_tokens']}",
            "total_token_count": f"Total token count: {total_token_count}",
            "model_name": llm_model_instance.MODEL_NAME,
        }

    def create_settings_ui(self):
        components = {}

        components["llm_provider"] = gr.Dropdown(
            value=self.llm_provider.CLASS_NAME,
            choices=llm.AVAILABLE_PROVIDERS_NAMES,  # type: ignore
            label="LLM Provider",
            container=True,
        )
        components["stream"] = gr.Checkbox(
            value=self.config.stream,
            label="Stream Response",
            interactive=True,
        )
        for provider_instance in self.list_of_llm_provider_instances:
            provider_instance.create_settings_ui()

        GradioBase.create_settings_event_listener(self.config, components)

        return components
