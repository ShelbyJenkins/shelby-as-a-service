from typing import Any, Iterator, List, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app.module_base import ModuleBase
from index.context_index_model import (
    ContextModel,
    DocDBConfigs,
    DocIngestTemplateConfigs,
    DomainModel,
    SourceModel,
)
from pydantic import BaseModel, Field
from services.document_loading.document_loading_providers import (
    GenericRecursiveWebScraper,
    GenericWebScraper,
)


class DocLoadingService(ModuleBase):
    CLASS_NAME: str = "doc_loading_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES: list[Type] = [GenericWebScraper, GenericRecursiveWebScraper]

    class ClassConfigModel(BaseModel):
        doc_loading_provider: str = "generic_web_scraper"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_names: list
    list_of_class_ui_names: list
    list_of_class_instances: list[Union[GenericWebScraper, GenericRecursiveWebScraper]]
    provider_instance: Any

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

    def load(self, data_source, doc_loading_provider=None):
        self.provider_instance = self.get_requested_class_instance(
            self.list_of_class_instances,
            doc_loading_provider
            if doc_loading_provider is not None
            else self.config.doc_loading_provider,
        )

        if self.provider_instance:
            return self.provider_instance._load(data_source.data_source_url)
        else:
            print("rnr")

    def create_settings_ui(self, current_class: Union[ContextModel, DomainModel, SourceModel]):
        components = {}
        provider_list = []
        with gr.Column():
            components["doc_loading_provider"] = gr.Dropdown(
                value=current_class.enabled_doc_ingest_template.loader_name,
                choices=self.list_of_class_names,
                label="Doc Loader",
                container=True,
            )
            for provider_instance in self.list_of_class_instances:
                if (
                    current_class.enabled_doc_ingest_template.loader_name
                    == provider_instance.CLASS_NAME
                ):
                    visibility = True
                else:
                    visibility = False
                with gr.Group(visible=visibility) as provider_settings:
                    provider_instance.create_settings_ui()

                provider_list.append(provider_settings)

            components["doc_loading_provider"].change(
                fn=self.set_current_provider,
                inputs=components["doc_loading_provider"],
                outputs=provider_list,
            )

            GradioHelper.create_settings_event_listener(self.config, components)

        return components

    def set_current_provider(self, requested_model):
        output = []
        for provider_instance in self.list_of_class_instances:
            if requested_model == provider_instance.CLASS_NAME:
                output.append(gr.Group(visible=True))
            else:
                output.append(gr.Group(visible=False))
        return output
