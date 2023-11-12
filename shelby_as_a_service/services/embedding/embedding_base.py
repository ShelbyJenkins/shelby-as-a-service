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

    def get_embedding_of_text(self, text: str, model_name: Optional[str] = None) -> list[float]:
        raise NotImplementedError

    def get_embeddings_from_list_of_texts(
        self, texts: list[str], model_name: Optional[str] = None
    ) -> list[list[float]]:
        raise NotImplementedError

    def get_model_instance(self, requested_model_name: str) -> Any:
        for model_name, model in self.MODEL_DEFINITIONS.items():
            if model_name == requested_model_name:
                model_instance = self.ModelConfig(**model)
                return model_instance

        raise ValueError(f"Requested model {requested_model_name} not found.")
