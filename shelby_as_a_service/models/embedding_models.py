from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class OpenAIEmbeddingModel:
    
    @dataclass
    class Ada002:
    
        model_name: str = "text-embedding-ada-002"
        tokens_max: int = 8192
        cost_per_k: float = 0.0001
    
    
    default_embedding_model: str = 'text-embedding-ada-002'
    available_models = [Ada002]

    openai_timeout_seconds: float = 180.0
    service_name_: str = "openai_embedding"

    required_variables_: List[str] = field(default_factory=list)
    required_secrets_: List[str] = field(default_factory=lambda: ["openai_api_key"])
