import typing
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.context_index.context_documents import IngestDoc
from services.context_index.context_index_model import (
    ChunkModel,
    DocumentModel,
    DomainModel,
    SourceModel,
)
from services.embedding.embedding_service import EmbeddingService

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class DatabaseBase(ABC, ModuleBase):
    DOC_DB_REQUIRES_EMBEDDINGS: bool

    @abstractmethod
    def get_index_domain_or_source_entry_count(
        self, source_name: Optional[str] = None, domain_name: Optional[str] = None
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def query_by_terms(self, search_terms: list[str] | str, domain_name: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_by_ids(self, ids: list[int] | int, domain_name: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def prepare_upsert_for_vectorstore(
        self,
        id: str,
        values: Optional[list[float]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, entries_to_upsert: list[dict[str, Any]], domain_name: str):
        raise NotImplementedError

    @abstractmethod
    def clear_existing_source(self, source_name: str, domain_name: str):
        raise NotImplementedError

    @abstractmethod
    def clear_existing_entries_by_id(
        self, doc_db_ids_requiring_deletion: list[str], domain_name: str
    ):
        raise NotImplementedError


class DatabaseService(ModuleBase):
    CLASS_NAME: str = "database_service"
    CLASS_UI_NAME: str = "Document Databases"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    def __init__(
        self,
        source: Optional[SourceModel] = None,
        domain: Optional[DomainModel] = None,
        doc_db_provider_name: Optional[AVAILABLE_PROVIDERS_NAMES] = None,
        doc_db_provider_config: dict[str, Any] = {},
        domain_name: Optional[str] = None,
    ):
        if source or domain:
            if source:
                self.source = source
                self.enabled_doc_db = source.enabled_doc_db
                self.domain = source.domain_model

            elif domain:
                self.enabled_doc_db = domain.enabled_doc_db
                self.domain = domain
            self.doc_db_provider_name = self.enabled_doc_db.name
            self.doc_db_provider_config = self.enabled_doc_db.config
            self.domain_name = self.domain.name
        elif doc_db_provider_name:
            self.doc_db_provider_name = doc_db_provider_name
            self.doc_db_provider_config = doc_db_provider_config
            self.domain_name = domain_name
        else:
            raise ValueError(
                "Must provide either SourceModel or DomainModel or doc_db_provider_name"
            )
        if not self.domain_name:
            raise ValueError("Must provide domain_name")

        self.doc_db_instance: DatabaseBase = self.get_requested_class_instance(
            requested_class_name=self.doc_db_provider_name,
            requested_class_config=self.doc_db_provider_config,
        )
        if self.doc_db_requires_embeddings:
            self.doc_embedder_service: EmbeddingService = EmbeddingService(
                source=self.source,
                doc_embedder_provider_name=self.enabled_doc_db.enabled_doc_embedder.name,
                doc_embedder_provider_config=self.enabled_doc_db.enabled_doc_embedder.config,
            )

    @property
    def doc_db_requires_embeddings(self) -> bool:
        return self.doc_db_instance.DOC_DB_REQUIRES_EMBEDDINGS

    def upsert_documents_from_context_index_source(self, upsert_docs: list[IngestDoc]):
        current_entry_count = self.doc_db_instance.get_index_domain_or_source_entry_count(
            source_name=self.source.name
        )
        chunks_to_upsert: list[ChunkModel] = []
        for doc in upsert_docs:
            if not doc.existing_document_model:
                raise ValueError(f"No existing_document_model for doc {doc.title}")
            if not doc.existing_document_model.context_chunks:
                raise ValueError(f"No context_chunks for doc {doc.title}")
            for i, chunk in enumerate(doc.existing_document_model.context_chunks):
                chunk_doc_db_id = f"id-{self.source.name}-{i + current_entry_count + 1}"
                chunk.chunk_doc_db_id = chunk_doc_db_id
                chunks_to_upsert.append(chunk)

        entries_to_upsert = []
        if self.doc_db_requires_embeddings:
            self.doc_embedder_service.get_document_embeddings_for_chunks_to_upsert(
                chunks_to_upsert=chunks_to_upsert
            )
            for chunk in chunks_to_upsert:
                metadata = chunk.prepare_upsert_metadata()
                entries_to_upsert.append(
                    self.doc_db_instance.prepare_upsert_for_vectorstore(
                        id=chunk.chunk_doc_db_id, values=chunk.chunk_embedding, metadata=metadata
                    )
                )
        else:
            raise NotImplementedError

        self.upsert(entries_to_upsert=entries_to_upsert)
        post_upsert_entry_count = self.doc_db_instance.get_index_domain_or_source_entry_count(
            source_name=self.source.name
        )
        if post_upsert_entry_count - current_entry_count != len(entries_to_upsert):
            raise ValueError(
                f"Upserted {len(entries_to_upsert)} entries but expected to upsert {post_upsert_entry_count - current_entry_count}"
            )
        self.log.info(
            f"Successfully upserted {len(entries_to_upsert)} entries to {self.doc_db_instance.CLASS_NAME}"
        )

    def clear_existing_entries_by_id(self, doc_db_ids_requiring_deletion: list[str]):
        existing_entry_count = self.doc_db_instance.get_index_domain_or_source_entry_count(
            source_name=self.source.name
        )
        self.doc_db_instance.clear_existing_entries_by_id(
            doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
            domain_name=self.domain_name,
        )
        post_delete_entry_count = self.doc_db_instance.get_index_domain_or_source_entry_count(
            source_name=self.source.name
        )
        if existing_entry_count - post_delete_entry_count != len(doc_db_ids_requiring_deletion):
            raise ValueError(
                f"Deleted {len(doc_db_ids_requiring_deletion)} entries but expected to delete {existing_entry_count - post_delete_entry_count}"
            )
        else:
            self.log.info(
                f"Deleted {len(doc_db_ids_requiring_deletion)} entries from {self.doc_db_instance.CLASS_NAME}"
            )

    def upsert(
        self,
        entries_to_upsert: list[dict[str, Any]],
    ):
        self.log.info(
            f"Upserting {len(entries_to_upsert)} entries to {self.doc_db_instance.CLASS_NAME}"
        )
        self.doc_db_instance.upsert(
            entries_to_upsert=entries_to_upsert, domain_name=self.domain_name
        )

    def query_by_terms(self, search_terms: list[str] | str) -> list[dict]:
        if isinstance(search_terms, str):
            search_terms = [search_terms]
        retrieved_docs = []
        for term in search_terms:
            docs = self.doc_db_instance.query_by_terms(
                search_terms=term, domain_name=self.domain_name
            )
            if docs:
                retrieved_docs.extend(docs)
            else:
                self.log.info(f"No documents found for {term}")
        return retrieved_docs

    def fetch_by_ids(self, ids: list[int] | int) -> list[dict]:
        if isinstance(ids, int):
            ids = [ids]

        docs = self.doc_db_instance.fetch_by_ids(ids=ids, domain_name=self.domain_name)
        if not docs:
            self.log.info(f"No documents found for {id}")
        return docs

    # def create_service_management_settings_ui(self):
    #     ui_components = {}

    #     with gr.Accordion(label="Pinecone"):
    #         pinecone_model_instance = self.context_index.get_or_create_doc_db_instance(
    #             name="pinecone_database"
    #         )
    #         pinecone_database = PineconeDatabase(config_file_dict=pinecone_model_instance.config)
    #         ui_components[
    #             "pinecone_database"
    #         ] = pinecone_database.create_provider_management_settings_ui()

    #     return ui_components

    @classmethod
    def create_service_ui_components(
        cls,
        parent_instance: Union[DomainModel, SourceModel],
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in cls.context_index.index.doc_dbs:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        enabled_doc_db_name = parent_instance.enabled_doc_db.name

        provider_select_dd, service_providers_dict = GradioHelpers.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=enabled_doc_db_name,
            required_classes=cls.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
