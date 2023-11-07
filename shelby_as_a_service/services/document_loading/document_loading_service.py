import abc
import typing
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from langchain.schema import Document
from services.context_index.context_index_model import DocumentModel, DomainModel, SourceModel

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class DocLoadingService(ABC, ModuleBase):
    CLASS_NAME: str = "doc_loader_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    #    metadata = {"source": url}
    #     soup = BeautifulSoup(raw_html, "html.parser")
    #     if title := soup.find("title"):
    #         metadata["title"] = title.get_text()
    #     if description := soup.find("meta", attrs={"name": "description"}):
    #         metadata["description"] = description.get("content", None)
    #     if html := soup.find("html"):
    #         metadata["language"] = html.get("lang", None)
    #     return metadata

    @classmethod
    def load_docs_from_source(
        cls,
        source: SourceModel,
    ) -> Optional[list[Document]]:
        return cls.load_docs_from_provider(
            uri=source.source_uri,
            provider_name=source.enabled_doc_loader.name,
            provider_config=source.enabled_doc_loader.config,
        )

    @classmethod
    def load_docs_from_provider(
        cls,
        uri: str,
        provider_name: AVAILABLE_PROVIDERS_NAMES,
        provider_config: dict[str, Any] = {},
        **kwargs,
    ) -> Optional[list[Document]]:
        provider: Type[DocLoadingService] = cls.get_requested_class(
            requested_class=provider_name, available_classes=cls.REQUIRED_CLASSES
        )

        docs = provider(config_file_dict=provider_config, **kwargs).load_docs(uri)
        if docs:
            cls.log.info(f"Total documents loaded from DocLoadingService: {len(docs)}")
            return docs

        cls.log.info(f"No data loaded for {uri}")
        return None

    @abstractmethod
    def load_docs(self, uri: str) -> Optional[list[Document]]:
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
