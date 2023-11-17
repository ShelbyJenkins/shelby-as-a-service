from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Optional, Type

import gradio as gr
import services.text_processing.prompts.prompt_template_service as prompts
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase
from services.service_base import ServiceBase


class LLMBase(ABC, ServiceBase):
    ModelConfig: BaseModel
    MODEL_DEFINITIONS: dict[str, Any]
    list_of_llm_provider_instances: list["LLMBase"] = []
    llm_model_instance: BaseModel
    MAX_RETRIES: int = 3

    class ClassConfigModel(BaseModel):
        current_llm_model_name: str = "gpt-3.5-turbo"

        class Config:
            extra = "ignore"

    config: ClassConfigModel

    @staticmethod
    def get_prompt_length(prompt, llm_provider_name: str, llm_model_instance) -> int:
        if llm_provider_name == "openai_llm":
            return prompts.tiktoken_len_of_openai_prompt(
                prompt=prompt, llm_model_instance=llm_model_instance
            )
        else:
            raise ValueError(f"llm_provider_name {llm_provider_name} not found.")

    def get_available_request_tokens(
        self,
        llm_provider_name: str,
        prompt: list[dict[str, str]],
        model_token_utilization,
        llm_model_name: Optional[str] = None,
        context_to_response_ratio=0.00,
    ) -> tuple[int, int]:
        llm_provider_instance: LLMBase = self.get_requested_class_instance(
            requested_class=llm_provider_name,
            available_classes=self.list_of_llm_provider_instances,
        )
        if llm_model_name is None:
            llm_model_name = llm_provider_instance.config.current_llm_model_name
        if not isinstance(llm_model_name, str):
            raise ValueError(
                f"llm_model_name {llm_model_name} is not a string. It is a {type(llm_model_name)}."
            )
        llm_model_instance = self.get_model_instance(
            requested_model_name=llm_model_name,
            provider=llm_provider_instance,
        )
        total_prompt_tokens = self.get_prompt_length(
            prompt=prompt,
            llm_provider_name=llm_provider_name,
            llm_model_instance=llm_model_instance,
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

    def calculate_cost(self, total_token_count: int, llm_model_instance):
        # Convert numbers to Decimal
        COST_PER_K_decimal = Decimal(llm_model_instance.COST_PER_K)
        token_count_decimal = Decimal(total_token_count)

        # Perform the calculation using Decimal objects
        request_cost = COST_PER_K_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        self.total_cost += request_cost
        self.last_request_cost = request_cost
        print(f"Request cost: ${format(request_cost, 'f')}")
        print(f"Total cost: ${format(self.total_cost, 'f')}")

    def set_current_model(self, requested_model):
        output = []
        for model_name, _ in self.config.available_models.items():
            if model_name == requested_model:
                self.config.current_llm_model_name = model_name
                GradioBase.update_settings_file = True
                output.append(gr.Group(visible=True))
            else:
                output.append(gr.Group(visible=False))
        return output

    def generate_text(
        self,
        prompt: list[dict[str, str]],
        llm_model_instance,
        max_tokens: int,
    ):
        raise NotImplementedError

    def make_decision(
        self,
        prompt: list[dict[str, str]],
        llm_model_instance,
        logit_bias: dict[str, int],
        max_tokens: int,
    ):
        raise NotImplementedError

    def create_chat(
        self,
        prompt: list[dict[str, str]],
        llm_model_instance,
        max_tokens: int,
        stream: bool,
    ):
        raise NotImplementedError

    def create_settings_ui(self):
        pass
