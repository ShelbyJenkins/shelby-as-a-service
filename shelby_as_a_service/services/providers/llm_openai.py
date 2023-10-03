from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional, Type

import modules.prompt_templates as PromptTemplates
import modules.text_processing.text as TextProcess
import openai
from pydantic import BaseModel
from services.providers.provider_base import ProviderBase


class OpenAILLM(ProviderBase):
    class OpenAILLMModel(BaseModel):
        model_name: str
        tokens_max: int
        cost_per_k: float

    required_secrets: List[str] = ["openai_api_key"]

    provider_name: str = "openai_llm"
    provider_ui_name: str = "openai_llm"

    ui_model_names = [
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]
    type_model: str = "openai_llm_model"
    available_models: List[OpenAILLMModel] = [
        OpenAILLMModel(model_name="gpt-4", tokens_max=8192, cost_per_k=0.06),
        OpenAILLMModel(model_name="gpt-4-32k", tokens_max=32768, cost_per_k=0.06),
        OpenAILLMModel(model_name="gpt-3.5-turbo", tokens_max=4096, cost_per_k=0.03),
        OpenAILLMModel(
            model_name="gpt-3.5-turbo-16k", tokens_max=16384, cost_per_k=0.03
        ),
    ]
    default_model: str = "gpt-3.5-turbo"

    openai_timeout_seconds: float = 180.0
    max_response_tokens: int = 300

    def __init__(self, parent_service=None):
        super().__init__(parent_service=parent_service)

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
        cost_per_k_decimal = Decimal(model.cost_per_k)
        token_count_decimal = Decimal(token_count)

        # Perform the calculation using Decimal objects
        request_cost = cost_per_k_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        self.app.total_cost += request_cost
        self.app.last_request_cost = request_cost
        print(f"Request cost: ${format(request_cost, 'f')}")
        print(f"Total cost: ${format(self.app.total_cost, 'f')}")

    def _calculate_cost_streaming(self, total_token_count, model):
        # Convert numbers to Decimal
        cost_per_k_decimal = Decimal(model.cost_per_k)
        token_count_decimal = Decimal(total_token_count)

        # Perform the calculation using Decimal objects
        request_cost = cost_per_k_decimal * (token_count_decimal / 1000)

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
            model=model.model_name,
            messages=prompt,
            max_tokens=self.max_response_tokens,
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
            model=model.model_name,
            messages=prompt,
            max_tokens=self.max_response_tokens,
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
                    delta_content, model.model_name
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
    ):
        model = self.get_model(self.type_model, model_name=llm_model)
        if model is None:
            return None, None, None
        if not prompt_template_path:
            prompt_template_path = "Answer in peace my friend."
        prompt = PromptTemplates.create_openai_prompt(
            query=query,
            prompt_template_dir=self.prompt_template_dir,
            prompt_template_path=prompt_template_path,
            documents=documents,
        )

        result = ""
        for entry in prompt:
            role = entry.get("role", "")
            content = entry.get("content", "")
            result += f"{role}: {content}\n"
        request_token_count = TextProcess.tiktoken_len(
            result, encoding_model=model.model_name
        )
        return prompt, model, request_token_count
