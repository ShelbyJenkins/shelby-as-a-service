from models.app_base import AppBase
from models.provider_models import LLMs

class LLMService(AppBase):
    
    model_ = LLMs()
    required_services_ = None
    
    def __init__(self):
        super().__init__()
        self.setup_config()
        
        
    def check_response(self, response):
        # Check if keys exist in dictionary
        parsed_response = (
            response.get("choices", [{}])[0].get("message", {}).get("content")
        )

        self.total_prompt_tokens += int(response.get("usage").get("prompt_tokens", 0))
        self.total_completion_tokens += int(
            response.get("usage").get("completion_tokens", 0)
        )

        if not parsed_response:
            raise ValueError(f"Error in response: {response}")

        return parsed_response

    def calculate_cost(self):
        prompt_cost = 0.03 * (self.total_prompt_tokens / 1000)
        completion_cost = 0.06 * (self.total_completion_tokens / 1000)
        total_cost = prompt_cost + completion_cost
        # total_cost = math.ceil(total_cost * 100) / 100
        return total_cost