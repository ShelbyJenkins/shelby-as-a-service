from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from langchain.schema import Document
from services.context_index.context_documents import IngestDoc
from services.context_index.context_index_model import DomainModel, SourceModel
from services.service_base import ServiceBase

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class DocLoadingService(ABC, ServiceBase):
    CLASS_NAME: str = "doc_loader_service"
    CONTEXT_INDEX_PROVIDER_KEY: str = "enabled_doc_loader"
    CLASS_UI_NAME: str = "Document Loading Service"
    AVAILABLE_PROVIDERS: list[Type] = AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    @classmethod
    def load_service_from_context_index(
        cls, domain_or_source: DomainModel | SourceModel
    ) -> "DocLoadingService":
        return cls.get_instance_from_context_index(domain_or_source=domain_or_source)

    def load_docs_from_context_index_source(
        self,
    ) -> Optional[list[IngestDoc]]:
        self.check_for_source

        docs = self.load_docs(
            uri=self.source.source_uri,
        )
        if not docs:
            self.log.info(f"No documents found for {self.source.name} @ {self.source.source_uri}")
            return None
        ingest_docs = []
        for doc in docs:
            ingest_docs.append(
                IngestDoc.create_ingest_doc_from_langchain_document(doc=doc, source=self.source)
            )
        return ingest_docs

    def load_docs(
        self,
        uri: str,
    ) -> Optional[list[Document]]:
        docs = self.load_docs_with_provider(uri)
        if not docs:
            self.log.info(f"No documents loaded from DocLoadingService: {self.__class__.__name__}")
            return None
        self.log.info(f"Total documents loaded from DocLoadingService: {len(docs)}")
        return docs

    @abstractmethod
    def load_docs_with_provider(self, uri: str) -> Optional[list[Document]]:
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

        enabled_doc_loader_name = parent_instance.enabled_doc_loader.name

        provider_select_dd, service_providers_dict = GradioHelpers.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=enabled_doc_loader_name,
            required_classes=cls.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
