from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional, Tuple, Type

import modules.prompt_templates as PromptTemplates
import modules.text_processing.text as TextProcess
import openai
from app_base import AppBase
from pydantic import BaseModel
from services.providers.provider_base import ProviderBase


class ProviderConfig(BaseModel):
    openai_timeout_seconds: float = 180.0
    max_response_tokens: int = 300


class OpenAILLM(ProviderBase):
    config: ProviderConfig

    class OpenAILLMModel(BaseModel):
        MODEL_NAME: str
        TOKENS_MAX: int
        COST_PER_K: float

    REQUIRED_SECRETS: List[str] = ["openai_api_key"]

    PROVIDER_NAME: str = "openai_llm"
    PROVIDER_UI_NAME: str = "openai_llm"

    UI_MODEL_NAMES = [
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    TYPE_MODEL: str = "openai_llm_model"
    AVAILABLE_MODELS: List[OpenAILLMModel] = [
        OpenAILLMModel(MODEL_NAME="gpt-4", TOKENS_MAX=8192, COST_PER_K=0.06),
        OpenAILLMModel(MODEL_NAME="gpt-4-32k", TOKENS_MAX=32768, COST_PER_K=0.06),
        OpenAILLMModel(MODEL_NAME="gpt-3.5-turbo", TOKENS_MAX=4096, COST_PER_K=0.03),
        OpenAILLMModel(
            MODEL_NAME="gpt-3.5-turbo-16k", TOKENS_MAX=16384, COST_PER_K=0.03
        ),
    ]

    def __init__(self, parent_class=None):
        super().__init__(parent_class=parent_class)
        self.config = AppBase.load_service_config(
            class_instance=self, config_class=ProviderConfig
        )

    def _check_response(self, response, model):
        # Check if keys exist in dictionary
        parsed_response = (
            response.get("choices", [{}])[0].get("message", {}).get("content")
        )

        total_prompt_tokens = int(response.get("usage").get("prompt_tokens", 0))
        total_completion_tokens = int(response.get("usage").get("completion_tokens", 0))

        if not parsed_response:
            raise ValueError(f"Error in response: {response}")

        token_count = total_prompt_tokens + total_completion_tokens
        self._calculate_cost(token_count, model=model)

        return (
            parsed_response,
            total_prompt_tokens,
            total_completion_tokens,
            token_count,
        )

    def _calculate_cost(self, token_count, model):
        # Convert numbers to Decimal
        COST_PER_K_decimal = Decimal(model.COST_PER_K)
        token_count_decimal = Decimal(token_count)

        # Perform the calculation using Decimal objects
        request_cost = COST_PER_K_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        self.app.total_cost += request_cost
        self.app.last_request_cost = request_cost
        print(f"Request cost: ${format(request_cost, 'f')}")
        print(f"Total cost: ${format(self.app.total_cost, 'f')}")

    def _calculate_cost_streaming(self, total_token_count, model):
        # Convert numbers to Decimal
        COST_PER_K_decimal = Decimal(model.COST_PER_K)
        token_count_decimal = Decimal(total_token_count)

        # Perform the calculation using Decimal objects
        request_cost = COST_PER_K_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        self.app.total_cost += request_cost
        self.app.last_request_cost = request_cost
        print(f"Total cost: ${format(self.app.total_cost, 'f')}")

    def _create_chat(
        self, query, prompt_template_path=None, documents=None, llm_model=None
    ) -> Optional[str]:
        prompt, model, _ = self._prep_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            llm_model=llm_model,
        )
        response = openai.ChatCompletion.create(
            api_key=self.app.secrets["openai_api_key"],
            model=model.MODEL_NAME,
            messages=prompt,
            max_tokens=self.config.max_response_tokens,
        )

        (
            prompt_response,
            total_prompt_tokens,
            total_completion_tokens,
            token_count,
        ) = self._check_response(response, model)

        if not prompt_response:
            return None

        # request_token_string = f"Request token count: {total_prompt_tokens}"
        # response_token_string = f"Response token count: {total_completion_tokens}"
        # total_token_string = f"Total token count: {total_completion_tokens}"

        return prompt_response

    def _create_streaming_chat(
        self, query, prompt_template_path=None, documents=None, llm_model=None
    ) -> Generator[List[str], None, None]:
        prompt, model, request_token_count = self._prep_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            llm_model=llm_model,
        )
        if prompt is None or model is None or request_token_count is None:
            return None

        stream = openai.ChatCompletion.create(
            api_key=self.app.secrets["openai_api_key"],
            model=model.MODEL_NAME,
            messages=prompt,
            max_tokens=self.config.max_response_tokens,
            stream=True,
        )

        chunk = {}
        partial_message = ""
        request_token_string = f"Request token count: {request_token_count}"
        response_token_count = 0
        total_token_count = request_token_count
        for chunk in stream:
            delta_content = (
                chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            )
            if len(delta_content) != 0:
                chunk_token_count = TextProcess.tiktoken_len(
                    delta_content, model.MODEL_NAME
                )
                response_token_count += chunk_token_count
                response_token_string = f"Response token count: {response_token_count}"
                total_token_count += chunk_token_count
                total_token_string = f"Total token count: {total_token_count}"

                partial_message += delta_content
                yield [
                    partial_message,
                    request_token_string,
                    response_token_string,
                    total_token_string,
                ]
            finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
            if finish_reason:
                self._calculate_cost_streaming(
                    total_token_count=total_token_count,
                    model=model,
                )

    def _prep_chat(
        self, query, prompt_template_path=None, documents=None, llm_model=None
    ) -> Tuple[List[Dict[str, str]], OpenAILLMModel, int]:
        model = self.get_model(self.TYPE_MODEL, model_name=llm_model)
        if model is None:
            return None, None, None

        prompt = PromptTemplates.create_openai_prompt(
            query=query,
            prompt_template_dir=self.PROMPT_TEMPLATE_DIR,
            prompt_template_path=prompt_template_path,
            documents=documents,
        )

        result = ""
        for entry in prompt:
            role = entry.get("role", "")
            content = entry.get("content", "")
            result += f"{role}: {content}\n"
        request_token_count = TextProcess.tiktoken_len(
            result, encoding_model=model.MODEL_NAME
        )
        return prompt, model, request_token_count
