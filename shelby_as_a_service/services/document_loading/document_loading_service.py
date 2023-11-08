import abc
import typing
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
import services.text_processing.text_utils as text_utils
from app.module_base import ModuleBase
from langchain.schema import Document
from services.context_index.context_documents import IngestDoc
from services.context_index.context_index_model import DocumentModel, DomainModel, SourceModel

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES

#   @abstractmethod
#     def load_docs(self, uri: str) -> Optional[list[Document]]:
#         raise NotImplementedError


class DocLoadingService(ABC, ModuleBase):
    CLASS_NAME: str = "doc_loader_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES
    doc_loader_instance: "DocLoadingService"
    source: Optional[SourceModel] = None
    domain: Optional[DomainModel] = None

    def __init__(
        self,
        source: Optional[SourceModel] = None,
        doc_loader_provider_name: Optional[str] = None,
        doc_loader_provider_config: dict[str, Any] = {},
    ):
        if source:
            self.source = source
            self.enabled_doc_loader = source.enabled_doc_loader
            self.domain = source.domain_model
            self.doc_loader_provider_name = self.enabled_doc_loader.name
            self.doc_loader_provider_config = self.enabled_doc_loader.config
        elif doc_loader_provider_name:
            self.doc_db_provider_name = doc_loader_provider_name
            self.doc_db_provider_config = doc_loader_provider_config
        else:
            raise ValueError("Must provide either SourceModel or doc_loader_provider_name")
        self.doc_loader_instance: DocLoadingService = self.get_requested_class_instance(
            requested_class_name=self.doc_loader_provider_name,
            requested_class_config=self.doc_loader_provider_config,
        )

    def load_docs_from_context_index_source(
        self,
        source: SourceModel,
    ) -> list[IngestDoc]:
        return self.load_docs(
            uri=source.source_uri,
        )

    def load_docs(
        self,
        uri: str,
    ) -> list[Document] | Document:
        docs = self.doc_loader_instance.load_docs(uri)
        if docs:
            self.log.info(f"Total documents loaded from DocLoadingService: {len(docs)}")
            return docs

        raise ValueError(f"No data loaded for {uri}")

    # metadata = {
    #     "domain_name": domain_name,
    #     "source_name": source_name,
    #     "context_chunk": context_chunk,
    #     "document_id": document_id,
    #     "title": title,
    #     "uri": uri,
    #     "source_type": source_type,
    #     "date_of_creation": date_of_creation,
    # }

    def create_ingest_docs(self, docs: list[Document] | Document) -> list[IngestDoc]:
        ingest_docs = []
        for doc in docs:
            ingest_docs.append()

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

        enabled_doc_loader_name = parent_instance.enabled_doc_loader.name

        provider_select_dd, service_providers_dict = GradioHelpers.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=enabled_doc_loader_name,
            required_classes=cls.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
