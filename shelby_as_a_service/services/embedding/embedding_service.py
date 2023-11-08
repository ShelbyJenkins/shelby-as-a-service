import typing
from abc import ABC, abstractmethod
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from langchain.schema import Document
from services.context_index.context_documents import IngestDoc
from services.context_index.context_index_model import (
    ChunkModel,
    DocumentModel,
    DomainModel,
    SourceModel,
)

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class EmbeddingBase(ABC, ModuleBase):
    @abstractmethod
    def get_embedding_of_text(self, text: str, model_name: Optional[str] = None) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def get_embeddings_from_list_of_texts(
        self, texts: list[str], model_name: Optional[str] = None
    ) -> list[list[float]]:
        raise NotImplementedError


class EmbeddingService(ModuleBase):
    CLASS_NAME: str = "embedding_service"
    CLASS_UI_NAME: str = "Embedding Service"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    def __init__(
        self,
        source: Optional[SourceModel] = None,
        doc_embedder_provider_name: Optional[AVAILABLE_PROVIDERS_NAMES] = None,
        doc_embedder_provider_config: dict = {},
    ):
        if source:
            self.source = source
            self.enabled_doc_embedder = self.source.enabled_doc_db.enabled_doc_embedder
            self.doc_embedder_provider_name = self.enabled_doc_embedder.name
            self.doc_embedder_provider_config = self.enabled_doc_embedder.config
        elif doc_embedder_provider_name:
            self.doc_embedder_provider_name = doc_embedder_provider_name
            self.doc_embedder_provider_config = doc_embedder_provider_config

        else:
            raise ValueError(
                "Must provide either source or doc_embedder_provider_name and doc_embedder_provider_config"
            )

        self.doc_embedder_instance: EmbeddingBase = self.get_requested_class_instance(
            requested_class_name=self.doc_embedder_provider_name,
            requested_class_config=self.doc_embedder_provider_config,
        )

    def get_embedding_of_text(
        self,
        text: str,
        model_name: Optional[str] = None,
    ) -> list[float]:
        text_embedding = self.doc_embedder_instance.get_embedding_of_text(
            text=text, model_name=model_name
        )
        if text_embedding is None:
            raise ValueError("No embedding returned")
        return text_embedding

    def get_embeddings_from_list_of_texts(
        self,
        texts: list[str],
        model_name: Optional[str] = None,
    ) -> list[list[float]]:
        text_embeddings = self.doc_embedder_instance.get_embeddings_from_list_of_texts(
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

    def create_settings_ui(self):
        components = {}

        components["embedding_provider"] = gr.Dropdown(
            value=GradioHelpers.get_class_ui_name_from_str(
                self.list_of_required_class_instances, self.config.embedding_provider
            ),
            choices=GradioHelpers.get_list_of_class_ui_names(self.list_of_required_class_instances),
            label=self.CLASS_UI_NAME,
            container=True,
            min_width=0,
        )

        for doc_embedder_instance in self.list_of_required_class_instances:
            doc_embedder_instance.create_settings_ui()

        GradioHelpers.create_settings_event_listener(self.config, components)

        return components
