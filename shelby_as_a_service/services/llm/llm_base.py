from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Optional, Type

import gradio as gr
import services.text_processing.prompts.prompt_template_service as prompts
from pydantic import BaseModel
from services.gradio_interface.gradio_base import GradioBase
from services.service_base import ServiceBase


class ClassConfigModel(BaseModel):
    provider_model_name: str
    available_models: dict[str, Any]

    class Config:
        extra = "ignore"


class ModelConfig(BaseModel):
    MODEL_NAME: str
    TOKENS_MAX: int
    COST_PER_K: float
    TOKENS_PER_MESSAGE: int
    TOKENS_PER_NAME: int
    frequency_penalty: float
    max_tokens: int
    presence_penalty: float
    temperature: float
    top_p: float

    class Config:
        extra = "ignore"


class LLMBase(ABC, ServiceBase):
    MODEL_DEFINITIONS: dict[str, Any]
    list_of_llm_provider_instances: list["LLMBase"] = []
    llm_provider: "LLMBase"
    SAFETY_TOKENS: int = 10
    MAX_RETRIES: int = 3

    llm_model_instance: ModelConfig
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
        llm_provider: "LLMBase",
        prompt: list[dict[str, str]],
        token_utilization: float,
        context_to_response_ratio=0.00,
    ) -> tuple[int, int]:
        llm_model_instance = llm_provider.llm_model_instance
        total_prompt_tokens = self.get_prompt_length(
            prompt=prompt,
            llm_provider_name=llm_provider.CLASS_NAME,
            llm_model_instance=llm_model_instance,
        )

        available_tokens = llm_model_instance.TOKENS_MAX * (token_utilization)
        if context_to_response_ratio > 0.0:
            available_request_tokens = available_tokens * context_to_response_ratio
            max_response_tokens = available_request_tokens - total_prompt_tokens
        else:
            max_response_tokens = available_tokens - total_prompt_tokens
        # for safety in case of model changes
        while max_response_tokens > (llm_model_instance.TOKENS_MAX - self.SAFETY_TOKENS):
            max_response_tokens -= 1
        return int(total_prompt_tokens), int(max_response_tokens)

    def get_logit_bias_total_prompt_tokens(
        self,
        llm_provider: "LLMBase",
        prompt: list[dict[str, str]],
        logit_bias_response_tokens: int,
    ) -> int:
        llm_model_instance = llm_provider.llm_model_instance
        total_prompt_tokens = self.get_prompt_length(
            prompt=prompt,
            llm_provider_name=llm_provider.CLASS_NAME,
            llm_model_instance=llm_model_instance,
        )
        max_response_tokens = total_prompt_tokens + logit_bias_response_tokens
        # for safety in case of model changes
        if max_response_tokens > llm_model_instance.TOKENS_MAX - self.SAFETY_TOKENS:
            raise ValueError(
                f"max_response_tokens {max_response_tokens} is greater than available_tokens {llm_model_instance.TOKENS_MAX - self.SAFETY_TOKENS}."
            )
        return int(total_prompt_tokens)

    def calculate_cost(self, total_token_count: int, llm_model_instance: ModelConfig):
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
                self.config.provider_model_name = model_name
                GradioBase.update_settings_file = True
                output.append(gr.Group(visible=True))
            else:
                output.append(gr.Group(visible=False))
        return output

    def generate_text(
        self,
        prompt: list[dict[str, str]],
        max_tokens: int,
    ):
        raise NotImplementedError

    def make_decision(
        self,
        prompt: list[dict[str, str]],
        logit_bias: dict[str, int],
        max_tokens: int,
        n: int,
    ):
        raise NotImplementedError

    def create_chat(
        self,
        prompt: list[dict[str, str]],
        max_tokens: int,
        stream: bool,
    ):
        raise NotImplementedError

    def create_settings_ui(self):
        pass
