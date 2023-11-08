import typing
from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from langchain.schema import Document
from pydantic import BaseModel, Field
from services.context_index.context_documents import IngestDoc
from services.context_index.context_index_model import (
    ChunkModel,
    DocumentModel,
    DomainModel,
    SourceModel,
)
from services.text_processing.text_utils import (
    clean_text_content,
    extract_and_clean_title,
    hash_content,
    tiktoken_len,
)

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class IngestProcessingBase(ABC, ModuleBase):
    @abstractmethod
    def preprocess_document(self, doc: IngestDoc) -> IngestDoc:
        raise NotImplementedError

    @abstractmethod
    def create_chunks(
        self,
        text: str | dict,
    ) -> Optional[list[str]]:
        raise NotImplementedError


class IngestProcessingService(ModuleBase):
    CLASS_NAME: str = "doc_loader_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    successfully_chunked_counter: int = 0
    docs_token_counts: list[int] = []

    def __init__(
        self,
        source: Optional[SourceModel] = None,
        doc_ingest_processor_provider_name: Optional[AVAILABLE_PROVIDERS_NAMES] = None,
        doc_ingest_processor_provider_config: dict[str, Any] = {},
    ):
        if source:
            self.source = source
            self.enabled_doc_ingest_processor = source.enabled_doc_ingest_processor
            self.domain = source.domain_model
            self.doc_ingest_processor_provider_name = self.enabled_doc_ingest_processor.name
            self.doc_ingest_processor_provider_config = self.enabled_doc_ingest_processor.config
        elif doc_ingest_processor_provider_name:
            self.doc_db_provider_name = doc_ingest_processor_provider_name
            self.doc_db_provider_config = doc_ingest_processor_provider_config
        else:
            raise ValueError(
                "Must provide either SourceModel or doc_ingest_processor_provider_name"
            )
        self.doc_ingest_processor_instance: IngestProcessingBase = (
            self.get_requested_class_instance(
                requested_class_name=self.doc_ingest_processor_provider_name,
                requested_class_config=self.doc_ingest_processor_provider_config,
            )
        )

    def create_chunks(
        self,
        text: str | dict,
    ) -> Optional[list[str]]:
        doc_chunks = self.doc_ingest_processor_instance.create_chunks(text=text)
        if not doc_chunks:
            self.log.info(f"{text[:10]} produced no chunks")
            return None

        self.log.info(f"{text[:10]} produced {len(doc_chunks)} chunks")

        return doc_chunks

    def process_documents_from_context_index_source(
        self,
        ingest_docs: list[IngestDoc],
    ) -> tuple[list[IngestDoc], list[str]]:
        preprocessed_docs = []
        for doc in ingest_docs:
            preprocessed_docs.append(self.doc_ingest_processor_instance.preprocess_document(doc))

        self.get_existing_docs_from_context_index_source(preprocessed_docs)
        if not (docs_requiring_update := self.check_for_docs_requiring_update(preprocessed_docs)):
            self.log.info(f"No new data found for {self.source.name}")
            return [], []

        doc_db_ids_requiring_deletion: list[str] = []
        upsert_docs: list[IngestDoc] = []
        for doc in docs_requiring_update:
            self.log.info(f"Processing and chunking {doc.title}")
            if doc.cleaned_content is None:
                raise ValueError("doc.cleaned_content must not be None")
            text_chunks = self.create_chunks(text=doc.cleaned_content)
            if not text_chunks:
                self.log.info(f"🔴 Skipping doc because text_chunks is None")
                continue
            doc_db_ids_requiring_deletion.extend(self.clear_and_get_existing_doc_db_chunks(doc))
            upsert_docs.append(self.create_document_and_chunk_models(text_chunks, doc))

        self.context_index.session.commit()
        self.log.info(f"Min: {min(self.docs_token_counts)}")
        self.log.info(f"Avg: {int(sum(self.docs_token_counts) / len(self.docs_token_counts))}")
        self.log.info(f"Max: {max(self.docs_token_counts)}")
        self.log.info(f"Total tokens: {int(sum(self.docs_token_counts))}")
        self.log.info(f"Total documents processed: {len(upsert_docs)}")
        self.log.info(f"Total document chunks: {self.successfully_chunked_counter}")
        return upsert_docs, doc_db_ids_requiring_deletion

    def clear_and_get_existing_doc_db_chunks(self, ingest_doc: IngestDoc) -> list[str]:
        doc_db_ids = []
        if not ingest_doc.existing_document_model:
            return []
        for chunk in ingest_doc.existing_document_model.context_chunks:
            doc_db_ids.append(chunk.id)
            self.context_index.session.delete(chunk)
        return doc_db_ids

    def create_document_and_chunk_models(
        self, text_chunks: list[str], ingest_doc: IngestDoc
    ) -> IngestDoc:
        if not ingest_doc.existing_document_model:
            ingest_doc.existing_document_model = DocumentModel(
                source_id=self.source.id,
                cleaned_content=ingest_doc.cleaned_content,
                hashed_cleaned_content=ingest_doc.hashed_cleaned_content,
                title=ingest_doc.title,
                uri=ingest_doc.uri,
                batch_update_enabled=self.source.batch_update_enabled,
                source_type=ingest_doc.source_type,
                date_published=ingest_doc.date_published,
            )
        for chunk in text_chunks:
            self.log.info(f"{ingest_doc.title} has {len(text_chunks)} chunks")
            ingest_doc.existing_document_model.context_chunks.append(
                ChunkModel(
                    chunked_content=chunk,
                )
            )
            self.successfully_chunked_counter += 1
            doc_token_count = [tiktoken_len(chunk) for chunk in text_chunks]
            self.log.info(
                f"🟢 Doc split into {len(text_chunks)} of averge length {int(sum(doc_token_count) / len(text_chunks))}"
            )
            self.docs_token_counts.extend(doc_token_count)

        return ingest_doc

    def check_for_docs_requiring_update(
        self, preprocessed_docs: list[IngestDoc]
    ) -> list[IngestDoc]:
        docs_requiring_update = []
        for doc in preprocessed_docs:
            if not doc.existing_document_model:
                docs_requiring_update.append(doc)
                continue
            if doc.hashed_cleaned_content != doc.existing_document_model.hashed_cleaned_content:
                docs_requiring_update.append(doc)

        self.log.info(f"Found {len(docs_requiring_update)} docs_requiring_update")
        return docs_requiring_update

    def get_existing_docs_from_context_index_source(
        self,
        ingest_docs: list[IngestDoc],
    ):
        existing_document_models = []
        for doc in ingest_docs:
            for document_model in self.source.documents:
                if doc.uri == document_model.uri:
                    doc.existing_document_id = document_model.id
                    doc.existing_document_model = document_model
                    existing_document_models.append(document_model)
                    break
            self.log.info(f"Found {len(existing_document_models)} existing_document_models")

    @classmethod
    def create_service_ui_components(
        cls,
        parent_instance: Union[DomainModel, SourceModel],
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in parent_instance.doc_loaders:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        text_processing_provider_name = parent_instance.enabled_doc_ingest_processor.name

        provider_select_dd, service_providers_dict = GradioHelpers.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=text_processing_provider_name,
            required_classes=cls.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
