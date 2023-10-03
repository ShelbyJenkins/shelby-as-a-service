from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Type

import modules.text_processing.text as text
import modules.utils.config_manager as ConfigManager
from langchain.embeddings import OpenAIEmbeddings
from services.providers.embedding_openai import OpenAIEmbedding
from services.service_base import ServiceBase


class EmbeddingService(ServiceBase):
    service_name: str = "embedding_service"
    service_ui_name: str = "embedding_service"
    provider_type: str = "embedding_provider"
    available_providers: List[Type] = [OpenAIEmbedding]
    default_provider: Type = OpenAIEmbedding

    def __init__(self, parent_agent=None):
        super().__init__(parent_agent=parent_agent)

        self.openai_embedding = OpenAIEmbedding(self)

    def get_query_embedding(self, query, provider_name=None, model_name=None):
        provider = self.get_provider(new_provider_name=provider_name)
        if provider:
            return provider._get_query_embedding(query, model_name=model_name)
        return None
