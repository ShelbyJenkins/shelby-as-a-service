from decimal import Decimal
from dataclasses import dataclass
from typing import List
from langchain.embeddings import OpenAIEmbeddings
from services.utils.app_base import AppBase
from services.data_processing.data_processing_service import TextProcessing


@dataclass
class EmbeddingModel:
    model_name: str
    tokens_max: int
    cost_per_k: float


class OpenAIEmbeddingService(AppBase):
    openai_timeout_seconds: float = 180.0

    default_model: str = "text-embedding-ada-002"
    available_models = [EmbeddingModel("text-embedding-ada-002", 8192, 0.0001)]

    def __init__(self, config_path=None, enabled_model=None):
        super().__init__(
            service_name_="openai_embedding",
            required_variables_=["default_model"],
            required_secrets_=["openai_api_key"],
            config_path=config_path,
        )
        self.model = self.set_model(enabled_model)

    def _get_query_embedding_from_provider(self, query):
        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            openai_api_key=self.secrets["openai_api_key"],
            model=self.model.model_name,
            request_timeout=self.openai_timeout_seconds,
        )
        query_embedding = embedding_retriever.embed_query(query)

        return query_embedding


class EmbeddingService(AppBase):
    default_provider: str = "openai_embedding"
    available_providers = [OpenAIEmbeddingService]

    def __init__(self, enabled_provider=None, enabled_model=None, config_path=None):
        super().__init__(
            service_name_="embedding_service",
            required_variables_=["default_provider"],
            config_path=config_path,
        )

        self.provider = self.set_provider(
            enabled_provider=enabled_provider, enabled_model=enabled_model
        )

    def get_query_embedding(self, query):
        token_count = TextProcessing.tiktoken_len(query, self.provider.model)

        self.calculate_cost(token_count)

        query_embedding = self.provider._get_query_embedding_from_provider(query)

        return query_embedding

    def calculate_cost(self, token_count):
        # Convert numbers to Decimal
        cost_per_k_decimal = Decimal(self.provider.model.cost_per_k)
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
