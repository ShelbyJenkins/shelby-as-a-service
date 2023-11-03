import typing
from typing import Any, Iterator, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from pydantic import BaseModel, Field
from services.context_index.context_index_model import ContextConfigModel
from services.document_loading.document_loading_providers import (
    GenericRecursiveWebScraper,
    GenericWebScraper,
)


class DocLoadingService(ModuleBase):
    CLASS_NAME: str = "doc_loader_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES = [GenericWebScraper, GenericRecursiveWebScraper]

    class ClassConfigModel(BaseModel):
        doc_loading_provider: str = "generic_web_scraper"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_names: list
    list_of_class_ui_names: list
    list_of_required_class_instances: list[Union[GenericWebScraper, GenericRecursiveWebScraper]]
    provider_instance: Union[GenericWebScraper, GenericRecursiveWebScraper]

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def load(self, data_source, doc_loading_provider=None):
        self.provider_instance = self.get_requested_class_instance(
            self.list_of_required_class_instances,
            doc_loading_provider
            if doc_loading_provider is not None
            else self.config.doc_loading_provider,
        )

        if self.provider_instance:
            return self.provider_instance._load(data_source.data_source_url)
        else:
            print("rnr")

    def create_service_ui_components(
        self, context_config: ContextConfigModel, groups_rendered: bool = True
    ):
        provider_configs_dict = {}

        for provider in doc_loaders:
            name = provider.provider_name
            config = provider.provider_config
            provider_configs_dict[name] = config

        enabled_provider_name = context_config.doc_loader.provider_name

        ui_components_dict = GradioHelpers.abstract_service_ui_components(
            enabled_provider_name=enabled_provider_name,
            required_classes=self.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return ui_components_dict
