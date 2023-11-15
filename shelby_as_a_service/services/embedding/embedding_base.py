import typing
from abc import ABC, abstractmethod
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

from pydantic import BaseModel
from services.service_base import ServiceBase


class EmbeddingBase(ABC, ServiceBase):
    ModelConfig: Type[BaseModel]
    config: BaseModel
    MODEL_DEFINITIONS: dict[str, Any]
    DOC_INDEX_KEY: str = "enabled_doc_embedder"

    def get_embedding_of_text_with_provider(
        self, text: str, embedding_model_instance
    ) -> list[float]:
        raise NotImplementedError

    def get_embeddings_from_list_of_texts_with_provider(
        self, texts: list[str], embedding_model_instance
    ) -> list[list[float]]:
        raise NotImplementedError
