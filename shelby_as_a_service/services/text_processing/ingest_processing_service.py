import typing
from typing import Any, Iterator, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from langchain.schema import Document
from pydantic import BaseModel, Field
from services.context_index.context_index_model import DomainModel, SourceModel

from .ingest_ceq import IngestCEQ
from .ingest_open_api import OpenAPIMinifier


class IngestProcessingService(ModuleBase):
    CLASS_NAME: str = "ingest_processing_service"
    CLASS_UI_NAME: str = "Ingest Processing Service"
    REQUIRED_CLASSES = [OpenAPIMinifier, IngestCEQ]

    @classmethod
    def create_class_instance(
        cls, requested_class: str
    ) -> Union[Type[OpenAPIMinifier], Type[IngestCEQ]]:
        for provider in cls.REQUIRED_CLASSES:
            if provider.CLASS_NAME == requested_class or provider.CLASS_UI_NAME == requested_class:
                return provider
        raise ValueError(f"Requested class {requested_class} not found.")

    @classmethod
    def process_documents(
        cls,
        docs: Iterator[Document],
        provider_name,
        provider_config: dict[str, Any] = {},
        **kwargs,
    ) -> Iterator[Document]:
        provider = cls.create_class_instance(requested_class=provider_name)
        return provider(config_file_dict=provider_config, **kwargs).process_documents(
            documents=docs
        )

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
