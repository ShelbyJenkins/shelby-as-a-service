import typing
from typing import Any, Iterator, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app.module_base import ModuleBase
from pydantic import BaseModel, Field
from services.context_index.context_index_model import (
    ContextConfigModel,
    ContextIndexModel,
    DocDBModel,
    DomainModel,
    SourceModel,
)
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
    provider_instance: Any

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

    def create_settings_ui(self, class_instance):
        provider_components = {}
        provider_views = []

        with gr.Column():
            doc_loading_provider = gr.Dropdown(
                value=class_instance.context_config.doc_loader.doc_loader_provider_name,
                choices=self.list_of_class_names,
                label="Doc Loader",
                container=True,
            )
            for provider_class in self.REQUIRED_CLASSES:
                provider_instance = provider_class()
                with gr.Group(visible=False) as provider_view:
                    provider_components[
                        provider_instance.CLASS_NAME
                    ] = provider_instance.create_settings_ui()

                provider_views.append(provider_view)

            doc_loading_provider.change(
                fn=self.set_current_ui_provider,
                inputs=doc_loading_provider,
                outputs=provider_views,
            )

        self.set_current_ui_provider(
            requested_model=class_instance.context_config.doc_loader.doc_loader_provider_name
        )
        return provider_components

    def set_current_ui_provider(self, requested_model: str):
        output = []
        for provider_name in self.list_of_class_names:
            if requested_model == provider_name:
                output.append(gr.Group(visible=True))
            else:
                output.append(gr.Group(visible=False))
        return output
