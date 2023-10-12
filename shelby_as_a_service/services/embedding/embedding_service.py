from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Type

import modules.text_processing.text as text
from pydantic import BaseModel
from services.embedding.embedding_openai import OpenAIEmbedding
from services.service_base import ServiceBase


class EmbeddingService(ServiceBase):
    SERVICE_NAME: str = "embedding_service"
    SERVICE_UI_NAME: str = "embedding_service"
    PROVIDER_TYPE: str = "embedding_provider"
    DEFAULT_PROVIDER: Type = OpenAIEmbedding
    AVAILABLE_PROVIDERS: List[Type] = [OpenAIEmbedding]

    class ServiceConfigModel(BaseModel):
        agent_select_status_message: str = "Search index to find docs related to request."

    config: ServiceConfigModel

    def __init__(self):
        super().__init__()

    def get_query_embedding(self, query, provider_name=None, model_name=None):
        provider = self.get_provider(new_provider_name=provider_name)
        if provider:
            return provider._get_query_embedding(query, model_name=model_name)
        return None
