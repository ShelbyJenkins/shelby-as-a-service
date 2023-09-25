from dataclasses import dataclass, field
from typing import List

@dataclass
class LLMs:
    
   
    @dataclass
    class GPT4:
    
        model_name: str = "gpt-4"
        tokens_max: int = 8192
        cost_per_k: float = 0.06
        
    @dataclass
    class GPT432k:
    
        model_name: str = "gpt-4-32k"
        tokens_max: int = 32768
        cost_per_k: float = 0.06
        
    @dataclass
    class GPT35:
    
        model_name: str = "gpt-3.5-turbo"
        tokens_max: int = 4096
        cost_per_k: float = 0.03
        
    @dataclass
    class GPT3516k:
    
        model_name: str = "gpt-3.5-turbo-16k"
        tokens_max: int = 16384
        cost_per_k: float = 0.03
    
    default_llm_model: str = "gpt-3.5-turbo"
    available_models = [GPT4, GPT432k, GPT35, GPT3516k]

    openai_timeout_seconds: float = 180.0
    
    service_name_: str = 'llm_service'
    
    required_variables_: List[str] = field(default_factory=list) 
    required_secrets_: List[str] = field(default_factory=lambda: ['openai_api_key'])

    

    
