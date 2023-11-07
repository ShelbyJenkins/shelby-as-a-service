import typing
from abc import ABC, abstractmethod
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from langchain.schema import Document
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


class EmbeddingService(EmbeddingBase):
    CLASS_NAME: str = "embedding_service"
    CLASS_UI_NAME: str = "Embedding Service"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES
    provider_instance: "EmbeddingService"

    def __init__(
        self,
        source: Optional[SourceModel],
        provider_name: Optional[AVAILABLE_PROVIDERS_NAMES] = None,
        provider_config: Optional[dict[str, Any]] = {},
        **kwargs,
    ):
        if source:
            provider_name = source.enabled_doc_db.name
            provider_config = source.enabled_doc_db.config

        if not provider_name or not provider_config:
            raise ValueError("Must provide either source or provider_name and provider_config")
        provider: Type[EmbeddingService] = self.get_requested_class(
            requested_class=provider_name, available_classes=self.REQUIRED_CLASSES
        )
        self.provider_instance = provider(config_file_dict=provider_config, **kwargs)

    def get_embedding_of_text_by_provider(
        self,
        text: str,
        model_name: Optional[str] = None,
        provider_name: Optional[AVAILABLE_PROVIDERS_NAMES] = None,
        provider_config: Optional[dict[str, Any]] = {},
        **kwargs,
    ) -> list[float]:
        if provider_name:
            provider: Type[EmbeddingService] = self.get_requested_class(
                requested_class=provider_name, available_classes=self.REQUIRED_CLASSES
            )
            self.provider_instance = provider(config_file_dict=provider_config, **kwargs)

        text_embedding = self.provider_instance.get_embedding_of_text(
            text=text, model_name=model_name
        )
        if text_embedding is None:
            raise ValueError("No embedding returned")
        return text_embedding

    def get_embeddings_from_list_of_texts_by_provider(
        self,
        texts: list[str],
        model_name: Optional[str] = None,
        provider_name: Optional[AVAILABLE_PROVIDERS_NAMES] = None,
        provider_config: Optional[dict[str, Any]] = {},
        **kwargs,
    ) -> list[list[float]]:
        if provider_name:
            provider: Type[EmbeddingService] = self.get_requested_class(
                requested_class=provider_name, available_classes=self.REQUIRED_CLASSES
            )
            self.provider_instance = provider(config_file_dict=provider_config, **kwargs)

        text_embeddings = self.provider_instance.get_embeddings_from_list_of_texts(
            texts=texts, model_name=model_name
        )
        if text_embeddings is None:
            raise ValueError("No embeddings returned")
        self.log.info(f"Got {len(text_embeddings)} embeddings")
        return text_embeddings

    def get_document_embeddings_from_document_models(
        self, document_models: list[DocumentModel]
    ) -> list[DocumentModel]:
        document_models_context_chunks = []
        document_models_text_embeddings = []
        for document_model in document_models:
            for chunk in document_model.context_chunks:
                document_models_context_chunks.append(chunk.context_chunk)

        document_models_text_embeddings = self.get_embeddings_from_list_of_texts(
            texts=document_models_context_chunks
        )
        if len(document_models_text_embeddings) != len(document_models_context_chunks):
            raise ValueError("Number of embeddings does not match number of context chunks")
        for i, document_model in enumerate(document_models):
            for chunk in document_model.context_chunks:
                chunk.chunk_embedding = document_models_context_chunks[i]
        return document_models

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

        for provider_instance in self.list_of_required_class_instances:
            provider_instance.create_settings_ui()

        GradioHelpers.create_settings_event_listener(self.config, components)

        return components
