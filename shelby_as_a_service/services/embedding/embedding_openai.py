import typing
from decimal import Decimal
from typing import Any, Literal, Optional, Type

import services.text_processing.text_utils as text_utils
from langchain.embeddings import OpenAIEmbeddings
from pydantic import BaseModel
from services.embedding.embedding_base import EmbeddingBase


class ClassConfigModel(BaseModel):
    provider_model_name: str = "text-embedding-ada-002"

    class Config:
        extra = "ignore"


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

        class Config:
            extra = "ignore"

    MODEL_DEFINITIONS: dict[str, Any] = {
        "text-embedding-ada-002": {
            "MODEL_NAME": "text-embedding-ada-002",
            "TOKENS_MAX": 8192,
            "COST_PER_K": 0.0001,
        }
    }

    class_config_model = ClassConfigModel
    config: ClassConfigModel

    def __init__(
        self,
        provider_model_name: Optional[str] = None,
        context_index_config: dict[str, Any] = {},
        config_file_dict: dict[str, Any] = {},
        **kwargs,
    ):
        if not provider_model_name:
            provider_model_name = kwargs.pop("provider_model_name", None)
        else:
            kwargs.pop("provider_model_name", None)
        if not provider_model_name:
            provider_model_name = ClassConfigModel.model_fields["provider_model_name"].default
        super().__init__(
            provider_model_name=provider_model_name,
            context_index_config=context_index_config,
            config_file_dict=config_file_dict,
            **kwargs,
        )
        if not self.current_provider_model_instance:
            raise ValueError("current_provider_model_instance not properly set!")
        self.embedding_model_instance: "OpenAIEmbedding.ModelConfig" = (
            self.current_provider_model_instance
        )

    def get_embedding_of_text_with_provider(
        self,
        text: str,
    ) -> list[float]:
        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            api_key=self.secrets["openai_api_key"],
            model=self.embedding_model_instance.MODEL_NAME,
            request_timeout=self.OPENAI_TIMEOUT_SECONDS,  # type: ignore
        )

        text_embedding = embedding_retriever.embed_query(text)

        # self._calculate_cost(text_embedding, embedding_model_instance)

        return text_embedding

    def get_embeddings_from_list_of_texts_with_provider(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            api_key=self.secrets["openai_api_key"],
            model=self.embedding_model_instance.MODEL_NAME,
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
