from __future__ import annotations

import typing
from enum import Enum
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from langchain.schema import Document
from pydantic import BaseModel, Field
from services.context_index.context_index_model import DomainModel, SourceModel
from services.document_loading.email_fastmail import EmailFastmail
from services.document_loading.web import GenericRecursiveWebScraper, GenericWebScraper


class DocLoadingService(ModuleBase):
    CLASS_NAME: str = "doc_loader_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES: list[Type] = [GenericWebScraper, GenericRecursiveWebScraper, EmailFastmail]
    available_providers = Literal[
        GenericWebScraper.class_name,
        GenericRecursiveWebScraper.class_name,
        EmailFastmail.class_name,
    ]

    @classmethod
    def create_class_instance(
        cls, requested_class: str
    ) -> Union[Type[GenericWebScraper], Type[GenericRecursiveWebScraper], Type[EmailFastmail]]:
        for provider in cls.REQUIRED_CLASSES:
            if provider.CLASS_NAME == requested_class or provider.CLASS_UI_NAME == requested_class:
                return provider
        raise ValueError(f"Requested class {requested_class} not found.")

    @classmethod
    def load_docs(
        cls,
        uri: str,
        provider_name: available_providers,
        provider_config: dict[str, Any] = {},
        **kwargs,
    ) -> Iterator[Document]:
        provider = cls.create_class_instance(requested_class=provider_name)
        return provider(config_file_dict=provider_config, **kwargs)._load(uri)

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
