import typing
from decimal import Decimal
from typing import Any, Literal, Optional, Type

import services.text_processing.text_utils as text_utils
from langchain.embeddings import OpenAIEmbeddings
from pydantic import BaseModel
from services.embedding.embedding_base import EmbeddingBase


class OpenAIEmbedding(EmbeddingBase):
    class_name = Literal["openai_embedding"]
    CLASS_NAME: str = typing.get_args(class_name)[0]
    CLASS_UI_NAME: str = "OpenAI Embedding"
    REQUIRED_SECRETS: list[str] = ["openai_api_key"]

    OPENAI_TIMEOUT_SECONDS: float = 60

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
        current_embedding_model_name: str = "text-embedding-ada-002"

    config: ClassConfigModel

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def get_embedding_of_text_with_provider(
        self,
        text: str,
        embedding_model_instance: Optional["OpenAIEmbedding.ModelConfig"] = None,
    ) -> list[float]:
        if embedding_model_instance is None:
            model_instance: OpenAIEmbedding.ModelConfig = self.get_model_instance(
                requested_model_name=self.config.current_embedding_model_name,
                provider=self,
            )
        else:
            model_instance = embedding_model_instance
        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            api_key=self.secrets["openai_api_key"],
            model=model_instance.MODEL_NAME,
            request_timeout=self.OPENAI_TIMEOUT_SECONDS,  # type: ignore
        )

        text_embedding = embedding_retriever.embed_query(text)

        # self._calculate_cost(text_embedding, embedding_model_instance)

        return text_embedding

    def get_embeddings_from_list_of_texts_with_provider(
        self,
        texts: list[str],
        embedding_model_instance: Optional["OpenAIEmbedding.ModelConfig"] = None,
    ) -> list[list[float]]:
        if embedding_model_instance is None:
            model_instance: OpenAIEmbedding.ModelConfig = self.get_model_instance(
                requested_model_name=self.config.current_embedding_model_name,
                provider=self,
            )
        else:
            model_instance = embedding_model_instance
        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            api_key=self.secrets["openai_api_key"],
            model=model_instance.MODEL_NAME,
            request_timeout=self.OPENAI_TIMEOUT_SECONDS,  # type: ignore
        )

        text_embeddings = embedding_retriever.embed_documents(texts)
        # self._calculate_cost(query, model)

        return text_embeddings

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
