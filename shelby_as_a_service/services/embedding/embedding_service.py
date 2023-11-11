import typing
from abc import ABC, abstractmethod
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from services.context_index.doc_index_model import (
    ChunkModel,
    DocDBModel,
    DocEmbeddingModel,
    DocumentModel,
    DomainModel,
    SourceModel,
)
from services.service_base import ServiceBase

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class EmbeddingService(ABC, ServiceBase):
    CLASS_NAME: str = "embedding_service"
    DOC_INDEX_KEY: str = "enabled_doc_embedder"
    CLASS_UI_NAME: str = "Embedding Service"
    AVAILABLE_PROVIDERS: list[Type] = AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    @classmethod
    def load_service_from_context_index(
        cls, domain_or_source: DomainModel | SourceModel
    ) -> "EmbeddingService":
        return cls.init_instance_from_doc_index(domain_or_source=domain_or_source)

    def get_embedding_of_text(
        self,
        text: str,
        model_name: Optional[str] = None,
    ) -> list[float]:
        text_embedding = self.get_embedding_of_text_with_provider(text=text, model_name=model_name)
        if text_embedding is None:
            raise ValueError("No embedding returned")
        return text_embedding

    def get_embeddings_from_list_of_texts(
        self,
        texts: list[str],
        model_name: Optional[str] = None,
    ) -> list[list[float]]:
        text_embeddings = self.get_embeddings_from_list_of_texts_with_provider(
            texts=texts, model_name=model_name
        )
        if text_embeddings is None:
            raise ValueError("No embeddings returned")
        self.log.info(f"Got {len(text_embeddings)} embeddings")
        return text_embeddings

    def get_document_embeddings_for_chunks_to_upsert(self, chunks_to_upsert: list[ChunkModel]):
        upsert_chunks_text = []
        upsert_docs_text_embeddings = []
        for chunk in chunks_to_upsert:
            upsert_chunks_text.append(chunk.context_chunk)

        upsert_docs_text_embeddings = self.get_embeddings_from_list_of_texts(
            texts=upsert_chunks_text
        )
        if len(upsert_docs_text_embeddings) != len(upsert_chunks_text):
            raise ValueError("Number of embeddings does not match number of context chunks")

        for i, chunk in enumerate(chunks_to_upsert):
            chunk.chunk_embedding = upsert_docs_text_embeddings[i]

    @abstractmethod
    def get_embedding_of_text_with_provider(
        self, text: str, model_name: Optional[str] = None
    ) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def get_embeddings_from_list_of_texts_with_provider(
        self, texts: list[str], model_name: Optional[str] = None
    ) -> list[list[float]]:
        raise NotImplementedError
