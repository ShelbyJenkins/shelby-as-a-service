import typing
from decimal import Decimal
from typing import Any, Type

import services.text_processing.text_utils as text_utils
from app.module_base import ModuleBase
from langchain.embeddings import OpenAIEmbeddings
from pydantic import BaseModel


class OpenAIEmbedding(ModuleBase):
    CLASS_NAME: str = "openai_embedding"
    CLASS_UI_NAME: str = "OpenAI Embedding"
    REQUIRED_SECRETS: list[str] = ["openai_api_key"]
    MODELS_TYPE: str = "embedding_models"
    OPENAI_TIMEOUT_SECONDS: float = 180

    class ModelConfig(BaseModel):
        MODEL_NAME: str
        TOKENS_MAX: int
        COST_PER_K: float

    MODEL_DEFINITIONS: dict[str, Any] = {
        "text-embedding-ada-002": {
            "MODEL_NAME": "text-embedding-ada-002",
            "TOKENS_MAX": 8192,
            "COST_PER_K": 0.0001,
        }
    }

    class ClassConfigModel(BaseModel):
        enabled_model_name: str = "text-embedding-ada-002"
        available_models: dict[str, "OpenAIEmbedding.ModelConfig"]

    config: ClassConfigModel
    embedding_models: list
    current_model_class: ModelConfig

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def get_query_embedding(self, query, model_name=None) -> list[float]:
        model = self.get_model(requested_model_name=model_name)
        if model is None:
            return None

        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            openai_api_key=self.secrets["openai_api_key"],
            model=model.MODEL_NAME,
            request_timeout=self.OPENAI_TIMEOUT_SECONDS,
        )  # type: ignore

        query_embedding = embedding_retriever.embed_query(query)
        self._calculate_cost(query, model)
        self.log.info("Embeddings retrieved")

        return query_embedding

    def get_documents_embedding(self, documents, model_name=None) -> list[list[float]]:
        model = self.get_model(requested_model_name=model_name)

        if model is None:
            return None

        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            openai_api_key=self.secrets["openai_api_key"],
            model=model.MODEL_NAME,
            request_timeout=self.OPENAI_TIMEOUT_SECONDS,
        )  # type: ignore

        doc_embeddings = embedding_retriever.embed_documents(documents)
        # self._calculate_cost(query, model)
        self.log.info("Embeddings retrieved")

        return doc_embeddings

    def _calculate_cost(self, query, model):
        token_count = text_utils.tiktoken_len(query, model.MODEL_NAME)

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

    def create_settings_ui(self):
        pass
