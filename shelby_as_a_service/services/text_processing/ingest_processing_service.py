import typing
from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from langchain.schema import Document
from pydantic import BaseModel, Field
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


class IngestProcessingService(ModuleBase, ABC):
    CLASS_NAME: str = "doc_loader_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    @classmethod
    def process_document_with_provider(
        cls,
        content: str,
        provider_name: AVAILABLE_PROVIDERS_NAMES,
        provider_config: dict[str, Any] = {},
        **kwargs,
    ) -> Optional[list[str]]:
        provider: Type[IngestProcessingService] = cls.get_requested_class(
            requested_class=provider_name, available_classes=cls.REQUIRED_CLASSES
        )

        document_chunks = provider(config_file_dict=provider_config, **kwargs).process_document(
            content=content
        )
        if not document_chunks:
            cls.log.info(f"{content[:10]} produced no chunks")
            return None

        cls.log.info(f"{content[:10]} produced {len(document_chunks)} chunks")

        return document_chunks

    @classmethod
    def process_documents_from_context_index_source(
        cls,
        source: SourceModel,
        documents: list[Document],
    ) -> Optional[list[DocumentModel]]:
        document_models = IngestProcessingService.preprocess_documents_from_context_index_source(
            source=source,
            documents=documents,
        )
        # Checks against local docs if there are changes or new docs
        if (
            IngestProcessingService.compare_new_and_existing_docs_from_context_index_source(
                source=source,
                document_models=document_models,
            )
            == False
        ):
            cls.log.info(f"Skipping data_source: no new data found for {source.name}")
            for doc in document_models:
                cls.context_index.session.expunge(doc)
            return None

        successfully_chunked_counter: int = 0
        docs_token_counts: list[int] = []

        for doc in document_models:
            cls.log.info(f"Processing and chunking {doc.title}")
            document_chunks = cls.process_document_with_provider(
                content=doc.cleaned_content,
                provider_name=source.enabled_doc_ingest_processor.name,
                provider_config=source.enabled_doc_ingest_processor.config,
            )
            if document_chunks is None:
                continue
            for chunk in document_chunks:
                cls.log.info(f"{doc.title} has {len(document_chunks)} chunks")
                doc.context_chunks.append(
                    ChunkModel(
                        chunked_content=chunk,
                    )
                )
                successfully_chunked_counter += 1
                doc_token_count = [tiktoken_len(chunk) for chunk in document_chunks]
                cls.log.info(
                    f"🟢 Doc split into {len(document_chunks)} of averge length {int(sum(doc_token_count) / len(document_chunks))}"
                )
                docs_token_counts.extend(doc_token_count)

        cls.context_index.session.commit()
        cls.log.info(f"Min: {min(docs_token_counts)}")
        cls.log.info(f"Avg: {int(sum(docs_token_counts) / len(docs_token_counts))}")
        cls.log.info(f"Max: {max(docs_token_counts)}")
        cls.log.info(f"Total tokens: {int(sum(docs_token_counts))}")
        cls.log.info(f"Total documents processed: {len(document_models)}")
        cls.log.info(f"Total document chunks: {successfully_chunked_counter}")
        return document_models

    @classmethod
    def preprocess_documents_from_context_index_source(
        cls,
        source: SourceModel,
        documents: list[Document],
    ) -> list[DocumentModel]:
        processed_docs = []
        for doc in documents:
            cleaned_content = clean_text_content(doc.page_content)
            processed_docs.append(
                DocumentModel(
                    cleaned_content=cleaned_content,
                    hashed_cleaned_content=hash_content(cleaned_content),
                    title=extract_and_clean_title(doc, uri=doc.metadata.get("source", None)),
                    uri=doc.metadata.get("source", None),
                    source_id=source.id,
                )
            )
        return processed_docs

    @classmethod
    def compare_new_and_existing_docs_from_context_index_source(
        cls, source: SourceModel, document_models: list[DocumentModel]
    ) -> bool:
        has_changes = False
        # This will hold the titles of new or different chunks
        new_or_changed_docs = []
        for doc in document_models:
            if any(doc.uri == document.uri for document in source.documents):
                has_changes = True
                new_or_changed_docs.append(doc.title)
                continue
            doc_hash = hash_content(doc.cleaned_content)
            if any(
                hash_content(document.hashed_cleaned_content) == doc_hash
                for document in source.documents
            ):
                has_changes = True
                new_or_changed_docs.append(doc.title)
                continue

        if new_or_changed_docs:
            cls.log.info(f"Found {len(new_or_changed_docs)} new or changed documents")
        return has_changes

    @abstractmethod
    def process_document(self, content: str) -> Optional[list[str]]:
        raise NotImplementedError

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
