from decimal import Decimal
from typing import Any, List, Type

import services.text_processing.text as text
from app_config.app_base import AppBase
from langchain.embeddings import OpenAIEmbeddings
from pydantic import BaseModel


class OpenAIEmbedding(AppBase):
    MODULE_NAME: str = "openai_embedding"
    MODULE_UI_NAME: str = "openai_embedding"
    REQUIRED_SECRETS: List[str] = ["openai_api_key"]

    class OpenAIEmbeddingModel(BaseModel):
        MODEL_NAME: str
        TOKENS_MAX: int
        COST_PER_K: float

    AVAILABLE_MODELS: List[OpenAIEmbeddingModel] = [
        OpenAIEmbeddingModel(
            MODEL_NAME="text-embedding-ada-002", TOKENS_MAX=8192, COST_PER_K=0.0001
        )
    ]

    class ModuleConfigModel(BaseModel):
        model: str = "text-embedding-ada-002"
        chunk_size: int = 10
        openai_timeout_seconds: float = 180

    config: ModuleConfigModel

    UI_MODEL_NAMES = ["text-embedding-ada-002"]
    DEFAULT_MODEL: str = "text-embedding-ada-002"
    TYPE_MODEL: str = "openai_embedding_model"

    def __init__(self, config_file_dict={}, **kwargs):
        module_config_file_dict = config_file_dict.get(self.MODULE_NAME, {})
        self.config = self.ModuleConfigModel(**{**kwargs, **module_config_file_dict})
        self.set_secrets(self)

    def _get_query_embedding(self, query, model_name=None):
        model = self.get_model(self, requested_model_name=model_name)
        if model is None:
            return None
        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            openai_api_key=self.secrets["openai_api_key"],
            model=model.MODEL_NAME,
            request_timeout=self.config.openai_timeout_seconds,
        )  # type: ignore
        query_embedding = embedding_retriever.embed_query(query)
        self._calculate_cost(query, model)
        self.log.print_and_log("Embeddings retrieved")
        return query_embedding

    def _get_documents_embedding(self, documents, model_name=None):
        model = self.get_model(self, requested_model_name=model_name)
        if model is None:
            return None
        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            openai_api_key=self.secrets["openai_api_key"],
            model=model.MODEL_NAME,
            request_timeout=self.config.openai_timeout_seconds,
        )  # type: ignore
        doc_embeddings = embedding_retriever.embed_documents(documents)
        # self._calculate_cost(query, model)
        self.log.print_and_log("Embeddings retrieved")
        return doc_embeddings

    def _calculate_cost(self, query, model):
        token_count = text.tiktoken_len(query, model.MODEL_NAME)

        # Convert numbers to Decimal
        COST_PER_K_decimal = Decimal(model.COST_PER_K)
        token_count_decimal = Decimal(token_count)

        # Perform the calculation using Decimal objects
        request_cost = COST_PER_K_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")
        # Ensure total_cost_ is a Decimal as well; if it's not already, convert it
        if not isinstance(self.total_cost, Decimal):
            self.total_cost = Decimal(self.total_cost)

        self.total_cost += request_cost
        print(f"Total cost: ${format(self.total_cost, 'f')}")
