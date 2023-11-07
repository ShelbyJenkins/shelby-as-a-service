import typing
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.context_index.context_index_model import (
    ChunkModel,
    DocumentModel,
    DomainModel,
    SourceModel,
)
from services.embedding.embedding_service import EmbeddingService

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class DatabaseBase(ABC, ModuleBase):
    @abstractmethod
    def get_index_domain_or_source_entry_count(self, source_name: Optional[str] = None) -> int:
        raise NotImplementedError

    @abstractmethod
    def query_by_terms(
        self,
        search_terms,
        **kwargs,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_by_ids(
        self,
        ids: list[int] | int,
        **kwargs,
    ):
        raise NotImplementedError

    @abstractmethod
    def prepare_upsert(
        self,
        id: str,
        values: Optional[list[float]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def upsert(
        self,
        entries_to_upsert: list[dict[str, Any]],
    ):
        raise NotImplementedError

    @abstractmethod
    def clear_existing_source(self, source_name: str):
        raise NotImplementedError

    @property
    @abstractmethod
    def doc_db_requires_embeddings(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def doc_db_embeddings_config(self) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError


class DatabaseService(DatabaseBase):
    CLASS_NAME: str = "database_service"
    CLASS_UI_NAME: str = "Document Databases"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    doc_db_instance: "DatabaseService"
    doc_embedder_instance: EmbeddingService
    source: SourceModel

    def __init__(
        self,
        source: Optional[SourceModel],
        doc_db_provider_name: Optional[AVAILABLE_PROVIDERS_NAMES],
        doc_embedder_provider_name: Optional[EmbeddingService.AVAILABLE_PROVIDERS_NAMES],
        doc_db_provider_config: Optional[dict[str, Any]] = {},
        doc_embedder_provider_config: Optional[dict[str, Any]] = {},
        domain_name: Optional[str] = None,
        **kwargs,
    ):
        if source:
            self.source = source
            doc_db_provider_name = source.enabled_doc_db.name
            doc_db_provider_config = source.enabled_doc_db.config
            domain_name = source.domain_model.name

        if not doc_db_provider_name or not doc_db_provider_config:
            raise ValueError(
                "Must provide either source or doc_db_provider_name and doc_db_provider_config"
            )
        if not domain_name:
            raise ValueError("Must provide either source or domain_name")
        doc_db_provider: Type[DatabaseService] = self.get_requested_class(
            requested_class=doc_db_provider_name, available_classes=self.REQUIRED_CLASSES
        )
        self.doc_db_instance = doc_db_provider(
            domain_name=domain_name, config_file_dict=doc_db_provider_config, **kwargs
        )

        if self.doc_db_instance.doc_db_requires_embeddings:
            if source:
                doc_embedder_provider_name = source.enabled_doc_db.enabled_doc_embedder.name
                doc_embedder_provider_config = source.enabled_doc_db.enabled_doc_embedder.config
            if not doc_embedder_provider_name or not doc_embedder_provider_config:
                raise ValueError(
                    "Must provide either source or doc_embedder_provider_name and doc_embedder_provider_config"
                )

            doc_embedder_provider: Type[EmbeddingService] = self.get_requested_class(
                requested_class=doc_embedder_provider_name,
                available_classes=EmbeddingService.REQUIRED_CLASSES,
            )
            self.doc_embedder_instance = doc_embedder_provider(
                config_file_dict=doc_embedder_provider_config, **kwargs
            )

    @property
    def doc_db_requires_embeddings(self) -> bool:
        return self.doc_db_instance.doc_db_requires_embeddings

    @property
    def doc_db_embeddings_config(self):
        return self.doc_db_instance.doc_db_embeddings_config

    def get_index_domain_or_source_entry_count(self, source_name: Optional[str] = None) -> int:
        return self.doc_db_instance.get_index_domain_or_source_entry_count(source_name=source_name)

    def prepare_upsert(
        self,
        id: str,
        values: Optional[list[float]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return self.doc_db_instance.prepare_upsert(id=id, values=values, metadata=metadata)

    def upsert(
        self,
        entries_to_upsert: list[dict[str, Any]],
    ):
        self.log.info(
            f"Upserting {len(entries_to_upsert)} entries to {self.doc_db_instance.CLASS_NAME}"
        )
        self.doc_db_instance.upsert(entries_to_upsert=entries_to_upsert)

    def prepare_upsert_with_provider(
        self,
        id: str,
        domain_name: str,
        source_name: str,
        context_chunk: str,
        document_id: int,
        title: str,
        uri: str,
        source_type: str,
        date_of_creation: datetime,
        embedding: Optional[list[float]] = None,
    ) -> dict[str, Any]:
        metadata = {
            "domain_name": domain_name,
            "source_name": source_name,
            "context_chunk": context_chunk,
            "document_id": document_id,
            "title": title,
            "uri": uri,
            "source_type": source_type,
            "date_of_creation": date_of_creation,
        }
        return self.prepare_upsert(id=id, values=embedding, metadata=metadata)

    def upsert_documents_from_context_index_source(self, document_models: list[DocumentModel]):
        self.clear_existing_source(source_name=self.source.name)

        if self.doc_db_requires_embeddings:
            document_models = (
                self.doc_embedder_instance.get_document_embeddings_from_document_models(
                    document_models=document_models
                )
            )

        entries_to_upsert: list[dict[str, Any]] = []
        for doc in document_models:
            for i, chunk in enumerate(doc.context_chunks):
                entries_to_upsert.append(
                    self.prepare_upsert_with_provider(
                        id=f"id-{self.source.name}-{i}",
                        domain_name=self.source.domain_model.name,
                        source_name=self.source.name,
                        context_chunk=chunk.context_chunk,
                        document_id=doc.id,
                        title=doc.title,
                        uri=doc.uri,
                        source_type=self.source.source_type,
                        date_of_creation=doc.date_of_creation,
                        embedding=chunk.chunk_embedding,
                    )
                )

        self.upsert(entries_to_upsert=entries_to_upsert)

    def query_by_terms(self, search_terms: list[str] | str):
        if isinstance(search_terms, str):
            search_terms = [search_terms]
        retrieved_docs = []
        for term in search_terms:
            docs = self.doc_db_instance.query_by_terms(
                search_terms=term,
            )
            if docs:
                retrieved_docs.append(docs)
            else:
                self.log.info(f"No documents found for {term}")
        return retrieved_docs

    def fetch_by_ids(self, ids: list[int] | int):
        if isinstance(ids, int):
            ids = [ids]

        docs = self.doc_db_instance.fetch_by_ids(
            ids=ids,
        )
        if not docs:
            self.log.info(f"No documents found for {id}")
        return docs

    def clear_existing_source(self, source_name: str):
        self.doc_db_instance.clear_existing_source(source_name=source_name)

    def create_service_management_settings_ui(self):
        ui_components = {}

        with gr.Accordion(label="Pinecone"):
            pinecone_model_instance = self.context_index.get_or_create_doc_db_instance(
                name="pinecone_database"
            )
            pinecone_database = PineconeDatabase(config_file_dict=pinecone_model_instance.config)
            ui_components[
                "pinecone_database"
            ] = pinecone_database.create_provider_management_settings_ui()

        return ui_components

    def create_service_ui_components(
        self,
        parent_instance: Union[DomainModel, SourceModel],
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in self.context_index.index.doc_dbs:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        enabled_doc_db_name = parent_instance.enabled_doc_db.name

        provider_select_dd, service_providers_dict = GradioHelpers.abstract_service_ui_components(
            service_name=self.CLASS_NAME,
            enabled_provider_name=enabled_doc_db_name,
            required_classes=self.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
