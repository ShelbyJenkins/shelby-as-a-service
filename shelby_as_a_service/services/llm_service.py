from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List

import modules.prompt_templates as PromptTemplates
import modules.text_processing.text as TextProcess
import modules.utils.config_manager as ConfigManager
import openai
from services.service_base import ServiceBase


class OpenAILLM(ServiceBase):
    @dataclass
    class OpenAILLMModel:
        model_name: str
        tokens_max: int
        cost_per_k: float

    provider_name: str = "openai_llm"
    ui_model_names = [
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    type_model: str = "openai_llm_model"
    available_models: List[OpenAILLMModel] = [
        OpenAILLMModel("gpt-4", 8192, 0.06),
        OpenAILLMModel("gpt-4-32k", 32768, 0.06),
        OpenAILLMModel("gpt-3.5-turbo", 4096, 0.03),
        OpenAILLMModel("gpt-3.5-turbo-16k", 16384, 0.03),
    ]
    required_secrets: List[str] = ["openai_api_key"]

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
        self, query, prompt_template=None, documents=None, model_name=None
    ):
        prompt, model = self._prep_chat(
            query=query,
            prompt_template=prompt_template,
            documents=documents,
            model_name=model_name,
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
        request_token_string = f"Request token count: {total_prompt_tokens}"
        response_token_string = f"Response token count: {total_completion_tokens}"
        total_token_string = f"Total token count: {total_completion_tokens}"
        return (
            prompt_response,
            request_token_string,
            response_token_string,
            total_token_string,
        )

    def _create_streaming_chat(
        self, query, prompt_template_path=None, documents=None, model_name=None
    ):
        prompt, model, request_token_count = self._prep_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            model_name=model_name,
        )
        stream = openai.ChatCompletion.create(
            api_key=self.app.secrets["openai_api_key"],
            model=model.model_name,
            messages=prompt,
            max_tokens=self.max_response_tokens,
            stream=True,
        )

        # partial_message[-1][1] = ""
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
        self, query, prompt_template_path=None, documents=None, model_name=None
    ):
        model = self.get_model(self.type_model, model_name=model_name)
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
        request_token_count = TextProcess.tiktoken_len(result, model.model_name)
        return prompt, model, request_token_count


class LLMService(ServiceBase):
    service_name: str = "llm_service"
    provider_type: str = "llm_provider"
    available_providers: List[Any] = [OpenAILLM]

    default_provider: Any = OpenAILLM
    max_response_tokens: int = 300

    def __init__(self, parent_agent):
        super().__init__(parent_agent=parent_agent)

    def create_streaming_chat(
        self,
        query,
        prompt_template_path=None,
        documents=None,
        provider_name=None,
        model_name=None,
    ):
        provider = self.get_provider(new_provider_name=provider_name)
        if provider:
            yield from provider._create_streaming_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                documents=documents,
                model_name=model_name,
            )

    def create_chat(
        self,
        query,
        prompt_template_path=None,
        documents=None,
        provider_name=None,
        model_name=None,
    ):
        provider = self.get_provider(new_provider_name=provider_name)
        if provider:
            return provider._create_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                documents=documents,
                model_name=model_name,
            )
