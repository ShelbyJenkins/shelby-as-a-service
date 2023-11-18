from typing import Any, Optional, Type, Union

import context_index.doc_index as doc_index_models
import services.document_loading as document_loading
from context_index.doc_index.docs.context_docs import IngestDoc
from langchain.schema import Document
from services.document_loading.document_loading_base import DocLoadingBase
from services.gradio_interface.gradio_base import GradioBase


class DocLoadingService(DocLoadingBase):
    CLASS_NAME: str = "doc_loader_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES: list[Type] = document_loading.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = document_loading.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_TYPINGS = document_loading.AVAILABLE_PROVIDERS_TYPINGS

    def __init__(
        self,
        doc_loader_provider_name: document_loading.AVAILABLE_PROVIDERS_TYPINGS,
        context_index_config: dict[str, Any] = {},
        config_file_dict: dict[str, Any] = {},
        **kwargs,
    ):
        super().__init__(
            current_provider_name=doc_loader_provider_name,
            context_index_config=context_index_config,
            config_file_dict=config_file_dict,
            **kwargs,
        )
        if not self.current_provider_instance:
            raise ValueError("current_provider_instance not properly set!")

        self.current_doc_loader: DocLoadingBase = self.current_provider_instance

    def load_docs(
        self,
        uri: str,
    ) -> Optional[list[Document]]:
        docs = self.current_doc_loader.load_docs_with_provider(uri)
        if not docs:
            self.log.info(
                f"🔴 No documents loaded from DocLoadingService: {self.__class__.__name__}"
            )
            return None
        self.log.info(f"🟢 Total documents loaded from DocLoadingService: {len(docs)}")
        return docs

    def load_docs_from_context_index_source(
        self,
        source: doc_index_models.SourceModel,
    ) -> Optional[list[IngestDoc]]:
        docs = self.load_docs(uri=source.source_uri)
        if not docs:
            self.log.info(f"No documents found for {source.name} @ {source.source_uri}")
            return None
        ingest_docs = []
        for doc in docs:
            ingest_docs.append(
                IngestDoc.create_ingest_doc_from_langchain_document(doc=doc, source=source)
            )
        return ingest_docs

    @classmethod
    def create_doc_index_ui_components(
        cls,
        parent_instance: doc_index_models.DomainModel | doc_index_models.SourceModel,
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in parent_instance.doc_loaders:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        enabled_doc_loader_name = parent_instance.enabled_doc_loader.name

        provider_select_dd, service_providers_dict = GradioBase.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=enabled_doc_loader_name,
            required_classes=cls.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
