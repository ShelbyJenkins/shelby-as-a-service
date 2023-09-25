from decimal import Decimal
import openai
from models.app_base import AppBase
from models.llm_models import LLMs

class LLMService(AppBase):
    
    model_ = LLMs()
    required_services_ = None
    llm_model = None
    max_response_tokens = None
    
    def __init__(self, config, sprite_name):
        super().__init__()
        self.setup_config(config, sprite_name)
        
        
    def set_llm_model(self, llm_model, max_response_tokens):
        self.max_response_tokens = max_response_tokens
        for model in self.model_.available_models:
            if model.model_name == self.default_llm_model:
                self.llm_model = model
            if model.model_name == llm_model:
                self.llm_model = model
                break
        
    def check_response(self, response):
        # Check if keys exist in dictionary
        parsed_response = (
            response.get("choices", [{}])[0].get("message", {}).get("content")
        )

        total_prompt_tokens = int(response.get("usage").get("prompt_tokens", 0))
        total_completion_tokens = int(
            response.get("usage").get("completion_tokens", 0)
        )

        if not parsed_response:
            raise ValueError(f"Error in response: {response}")
        
        self.calculate_cost(total_prompt_tokens + total_completion_tokens)
        
        return parsed_response
    
    def calculate_cost(self, token_count):
    
        # Convert numbers to Decimal
        cost_per_k_decimal = Decimal(self.llm_model.cost_per_k)
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
        
    def create(self, prompt):
        
        response = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            model=self.llm_model.model_name,
            messages=prompt,
            max_tokens=self.max_response_tokens,
        )
        prompt_response = self.check_response(response)
        if not prompt_response:
            return None

        return prompt_response