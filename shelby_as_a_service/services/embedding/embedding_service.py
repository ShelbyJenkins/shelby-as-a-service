import typing
from abc import ABC, abstractmethod
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

import gradio as gr
import services.embedding as embedding
from services.context_index.doc_index.doc_index_model import (
    ChunkModel,
    DocDBModel,
    DocEmbeddingModel,
    DocumentModel,
    DomainModel,
    SourceModel,
)
from services.embedding.embedding_base import EmbeddingBase


class EmbeddingService(EmbeddingBase):
    CLASS_NAME: str = "embedding_service"

    CLASS_UI_NAME: str = "Embedding Service"
    AVAILABLE_PROVIDERS: list[Type] = embedding.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = embedding.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = embedding.AVAILABLE_PROVIDERS_NAMES

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
        text_embedding = self.get_embedding_of_text(text=text, model_name=model_name)
        if text_embedding is None:
            raise ValueError("No embedding returned")
        return text_embedding

    def get_embeddings_from_list_of_texts(
        self,
        texts: list[str],
        model_name: Optional[str] = None,
    ) -> list[list[float]]:
        text_embeddings = self.get_embeddings_from_list_of_texts(texts=texts, model_name=model_name)
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
