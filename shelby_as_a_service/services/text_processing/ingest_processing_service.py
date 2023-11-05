import typing
from typing import Any, Iterator, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from pydantic import BaseModel, Field
from services.context_index.context_index_model import DomainModel, SourceModel

from .ingest_ceq import IngestCEQ
from .ingest_open_api import OpenAPIMinifier


class IngestProcessingService(ModuleBase):
    CLASS_NAME: str = "ingest_processing_service"
    CLASS_UI_NAME: str = "Ingest Processing Service"
    REQUIRED_CLASSES = [OpenAPIMinifier, IngestCEQ]

    class ClassConfigModel(BaseModel):
        text_processing_provider: str = "ceq_ingest_processor"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_names: list
    list_of_class_ui_names: list
    list_of_required_class_instances: list[Union[OpenAPIMinifier, IngestCEQ]]
    provider_instance: Union[OpenAPIMinifier, IngestCEQ]

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def load(self, data_source, text_proc_provider=None):
        self.provider_instance = self.get_requested_class_instance(
            text_proc_provider
            if text_proc_provider is not None
            else self.config.text_processing_provider,
        )

        if self.provider_instance:
            return self.provider_instance._load(data_source.data_source_url)
        else:
            print("rnr")

    def create_service_ui_components(
        self,
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
            service_name=self.CLASS_NAME,
            enabled_provider_name=text_processing_provider_name,
            required_classes=self.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
