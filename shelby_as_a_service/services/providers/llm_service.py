from decimal import Decimal
from dataclasses import dataclass
from typing import List
import openai
from services.utils.app_base import AppBase


@dataclass
class LLMModel:
    model_name: str
    tokens_max: int
    cost_per_k: float

class OpenAILLMService(AppBase):
    openai_timeout_seconds: float = 180.0
    max_response_tokens = 300
    
    default_model: str = "gpt-3.5-turbo"
    available_models = [
        LLMModel("gpt-4", 8192, 0.06),
        LLMModel("gpt-4-32k", 32768, 0.06),
        LLMModel("gpt-3.5-turbo", 4096, 0.03),
        LLMModel("gpt-3.5-turbo-16k", 16384, 0.03),
    ]

    def __init__(self, enabled_model=None, config_path=None):
        super().__init__(
            service_name_="openai_llm",
            required_variables_=["default_llm_model"],
            required_secrets_=["openai_api_key"],
            config_path=config_path,
        )
        self.model = self.set_model(enabled_model=enabled_model)

    def _check_response(self, response):
        # Check if keys exist in dictionary
        parsed_response = (
            response.get("choices", [{}])[0].get("message", {}).get("content")
        )

        total_prompt_tokens = int(response.get("usage").get("prompt_tokens", 0))
        total_completion_tokens = int(response.get("usage").get("completion_tokens", 0))

        if not parsed_response:
            raise ValueError(f"Error in response: {response}")

        self._calculate_cost(total_prompt_tokens + total_completion_tokens)

        return parsed_response

    def _calculate_cost(self, token_count):
        # Convert numbers to Decimal
        cost_per_k_decimal = Decimal(self.model.cost_per_k)
        token_count_decimal = Decimal(token_count)

        # Perform the calculation using Decimal objects
        request_cost = cost_per_k_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        # Ensure total_cost is a Decimal as well; if it's not already, convert it
        if not isinstance(AppBase.total_cost, Decimal):
            AppBase.total_cost = Decimal(AppBase.total_cost)
        AppBase.total_cost += request_cost
        print(f"Total cost: ${format(AppBase.total_cost, 'f')}")

    def _create_chat(self, prompt):
        
        response = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            model=self.model.model_name,
            messages=prompt,
            max_tokens=self.max_response_tokens,
        )
        prompt_response = self._check_response(response)
        if not prompt_response:
            return None

        return prompt_response
    
    def _create_streaming_chat(self, prompt):
        partial_message = [
            ["", ""],
            ["", ""]
        ]

        stream = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            model=self.model.model_name,
            messages=prompt,
            max_tokens=self.max_response_tokens,
            stream=True,
        )
   
        partial_message[-1][1] = ""
        for chunk in stream:
            if len(chunk['choices'][0]['delta']['content']) != 0:
                partial_message[-1][1] += chunk['choices'][0]['delta']['content']
                yield partial_message

class LLMService(AppBase):
    max_response_tokens = 300

    default_provider: str = "openai_llm"
    available_providers = [OpenAILLMService]

    def __init__(self, config_path=None, enabled_provider=None, enabled_model=None):
        super().__init__(
            service_name_="llm_service",
            required_variables_=["max_response_tokens", "default_provider"],
            config_path=config_path,
        )

        self.provider = self.set_provider(enabled_provider, enabled_model)
        
    def create_chat(self, prompt):

        return self.provider._create_chat(prompt)
    
    def create_streaming_chat(self, prompt):

        return self.provider._create_streaming_chat(prompt)

             