from typing import Any, Dict, Generator, Optional, Type

import gradio as gr
import services.llm as llm
import services.text_processing.prompts.prompt_template_service as prompts
import services.text_processing.text_utils as text_utils
from services.llm.llm_base import LLMBase


class LLMService(LLMBase):
    CLASS_NAME: str = "llm_service"
    CLASS_UI_NAME: str = "LLM Settings"
    REQUIRED_CLASSES: list[Type] = llm.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list = llm.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = llm.AVAILABLE_PROVIDERS_NAMES

    list_of_llm_provider_instances: list[LLMBase] = []
    current_llm_provider: LLMBase

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.list_of_llm_provider_instances = self.list_of_required_class_instances
        llm_provider_name = kwargs.get("llm_provider_name", None)
        if llm_provider_name:
            self.current_llm_provider = self.get_requested_class_instance(
                requested_class=llm_provider_name,
                available_classes=self.list_of_llm_provider_instances,
            )

    def create_chat(
        self,
        prompt: list[Dict[str, str]],
        llm_provider_name: llm.AVAILABLE_PROVIDERS_NAMES,
        llm_model_name: str,
        model_token_utilization: float,
        logit_bias=None,
        stream: Optional[bool] = None,
    ):
        llm_provider_instance: LLMBase = self.get_requested_class_instance(
            requested_class=llm_provider_name,
            available_classes=self.list_of_llm_provider_instances,
        )

        total_prompt_tokens, max_tokens = self.get_available_request_tokens(
            prompt=prompt,
            model_token_utilization=model_token_utilization,
            llm_provider_name=llm_provider_name,
            llm_model_name=llm_model_name,
        )

        llm_model_instance = self.get_model_instance(
            requested_model_name=llm_model_name,
            llm_provider_instance=llm_provider_instance,
        )

        if max_tokens is None:
            max_tokens = llm_model_instance.max_tokens
        while max_tokens + total_prompt_tokens > (llm_model_instance.TOKENS_MAX - 15):
            max_tokens -= 1

        response = {}
        for response in llm_provider_instance.create_chat(
            prompt=prompt,
            llm_model_instance=llm_model_instance,
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
        llm_provider_name: llm.AVAILABLE_PROVIDERS_NAMES,
        prompt: list[Dict[str, str]],
        llm_model_name: str,
        model_token_utilization=0.5,
        context_to_response_ratio=0.00,
    ) -> tuple[int, int]:
        llm_provider_instance: LLMBase = self.get_requested_class_instance(
            requested_class=llm_provider_name,
            available_classes=self.list_of_llm_provider_instances,
        )
        llm_model_instance = self.get_model_instance(
            requested_model_name=llm_model_name,
            llm_provider_instance=llm_provider_instance,
        )
        total_prompt_tokens = self.get_prompt_length(
            prompt=prompt, llm_provider_name=llm_provider_name, llm_model_name=llm_model_name
        )
        available_tokens = llm_model_instance.TOKENS_MAX - 10  # for safety in case of model changes
        available_tokens = available_tokens * (model_token_utilization)
        if context_to_response_ratio > 0.0:
            available_request_tokens = available_tokens * context_to_response_ratio
            available_request_tokens = available_request_tokens - total_prompt_tokens
        else:
            available_request_tokens = available_tokens - total_prompt_tokens
        available_response_tokens = available_tokens - available_request_tokens
        max_tokens = available_response_tokens + available_request_tokens

        return int(available_request_tokens), int(max_tokens)

    def get_prompt_length(
        self, prompt, llm_provider_name: llm.AVAILABLE_PROVIDERS_NAMES, llm_model_name: str
    ) -> int:
        if llm_provider_name == llm.OpenAILLM.CLASS_NAME:
            return prompts.tiktoken_len_of_openai_prompt(
                prompt=prompt, llm_model_instance=llm_model_name
            )
        else:
            raise ValueError(f"llm_provider_name {llm_provider_name} not found.")

    def create_settings_ui(self):
        components = {}

        components["llm_provider"] = gr.Dropdown(
            value=self.current_llm_provider.CLASS_UI_NAME,
            choices=llm.AVAILABLE_PROVIDERS_NAMES,
            label="LLM Provider",
            container=True,
        )

        for provider_instance in self.list_of_llm_provider_instances:
            provider_instance.create_settings_ui()

        # GradioBase.create_settings_event_listener(cls.config, components)

        return components
