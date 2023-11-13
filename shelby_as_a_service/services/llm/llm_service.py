from typing import Any, Generator, Optional, Type

import gradio as gr
import services.llm as llm
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase
from services.llm.llm_base import LLMBase


class LLMService(LLMBase):
    CLASS_NAME: str = "llm_service"
    CLASS_UI_NAME: str = "LLM Settings"
    REQUIRED_CLASSES: list[Type] = llm.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list = llm.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_TYPINGS = llm.AVAILABLE_PROVIDERS_TYPINGS

    class ClassConfigModel(BaseModel):
        current_llm_provider_name: str = "openai_llm"
        enabled_llm_providers_names: list[str] = ["openai_llm"]  # Will use in the future
        stream: bool = False

    config: ClassConfigModel

    list_of_llm_provider_instances: list[LLMBase] = []
    current_llm_provider: LLMBase
    llm_model_instance: BaseModel

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.list_of_llm_provider_instances = self.list_of_required_class_instances
        current_llm_provider_name = kwargs.get(
            "llm_provider_name", self.config.current_llm_provider_name
        )
        if current_llm_provider_name:
            self.current_llm_provider = self.get_requested_class_instance(
                requested_class=current_llm_provider_name,
                available_classes=self.list_of_llm_provider_instances,
            )

    def generate_text(
        self,
        prompt: list[dict[str, str]],
        llm_provider_name: llm.AVAILABLE_PROVIDERS_TYPINGS,
        llm_model_name: str,
        model_token_utilization: float = 1,
        max_tokens: Optional[int] = None,
    ):
        llm_provider_instance: LLMBase = self.get_requested_class_instance(
            requested_class=llm_provider_name,
            available_classes=self.list_of_llm_provider_instances,
        )
        total_prompt_tokens, new_max_tokens = self.get_available_request_tokens(
            prompt=prompt,
            model_token_utilization=model_token_utilization,
            llm_provider_name=llm_provider_name,
            llm_model_name=llm_model_name,
        )
        if max_tokens is None:
            max_tokens = new_max_tokens

        llm_model_instance = self.get_model_instance(
            requested_model_name=llm_model_name,
            provider=llm_provider_instance,
        )

        # Already set in get_available_request_tokens, but here for safety
        while max_tokens + total_prompt_tokens > (llm_model_instance.TOKENS_MAX - 15):
            max_tokens -= 1

        response = llm_provider_instance.generate_text(
            prompt=prompt,
            llm_model_instance=llm_model_instance,
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
        llm_provider_name: llm.AVAILABLE_PROVIDERS_TYPINGS,
        llm_model_name: str,
        logit_bias: dict[str, int],
        max_tokens: int,
    ):
        llm_provider_instance: LLMBase = self.get_requested_class_instance(
            requested_class=llm_provider_name,
            available_classes=self.list_of_llm_provider_instances,
        )
        total_prompt_tokens, _ = self.get_available_request_tokens(
            prompt=prompt,
            model_token_utilization=1,
            llm_provider_name=llm_provider_name,
            llm_model_name=llm_model_name,
        )
        llm_model_instance = self.get_model_instance(
            requested_model_name=llm_model_name,
            provider=llm_provider_instance,
        )

        # Already set in get_available_request_tokens, but here for safety
        while max_tokens + total_prompt_tokens > (llm_model_instance.TOKENS_MAX - 15):
            max_tokens -= 1

        response = llm_provider_instance.make_decision(
            prompt=prompt,
            llm_model_instance=llm_model_instance,
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
        llm_provider_name: llm.AVAILABLE_PROVIDERS_TYPINGS,
        llm_model_name: Optional[str],
        model_token_utilization: float = 0.5,
        stream: Optional[bool] = None,
    ):
        llm_provider_instance: LLMBase = self.get_requested_class_instance(
            requested_class=llm_provider_name,
            available_classes=self.list_of_llm_provider_instances,
        )
        if llm_model_name is None:
            llm_model_name = llm_provider_instance.config.current_llm_model_name

        total_prompt_tokens, max_tokens = self.get_available_request_tokens(
            prompt=prompt,
            model_token_utilization=model_token_utilization,
            llm_provider_name=llm_provider_name,
            llm_model_name=llm_model_name,
        )

        llm_model_instance = self.get_model_instance(
            requested_model_name=llm_model_name,
            provider=llm_provider_instance,
        )

        # For safety
        while max_tokens + total_prompt_tokens > (llm_model_instance.TOKENS_MAX - 15):
            max_tokens -= 1

        response = {}
        for response in llm_provider_instance.create_chat(
            prompt=prompt,
            llm_model_instance=llm_model_instance,
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
            value=self.current_llm_provider.CLASS_NAME,
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
