from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Type

import services.text_processing.text as text
from app_config.app_base import AppBase
from pydantic import BaseModel
from services.embedding.embedding_openai import OpenAIEmbedding


class EmbeddingService(AppBase):
    MODULE_NAME: str = "embedding_service"
    MODULE_UI_NAME: str = "embedding_service"
    PROVIDER_TYPE: str = "embedding_provider"
    DEFAULT_PROVIDER: Type = OpenAIEmbedding
    REQUIRED_MODULES: List[Type] = [OpenAIEmbedding]

    class ModuleConfigModel(BaseModel):
        agent_select_status_message: str = "Search index to find docs related to request."

    config: ModuleConfigModel

    def __init__(self):
        super().__init__()

    def get_query_embedding(self, query, provider_name=None, model_name=None):
        provider = self.get_provider(new_provider_name=provider_name)
        if provider:
            return provider._get_query_embedding(query, model_name=model_name)
        return None
