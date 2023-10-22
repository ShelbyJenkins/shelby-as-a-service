from typing import Any, Iterator, List, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app.module_base import ModuleBase
from pydantic import BaseModel, Field
from services.document_loading.document_loading_providers import GenericRecursiveWebScraper, GenericWebScraper


class DocLoadingService(ModuleBase):
    CLASS_NAME: str = "doc_loading_service"
    CLASS_UI_NAME: str = "Document Loading Service"
    REQUIRED_CLASSES: List[Type] = [GenericWebScraper, GenericRecursiveWebScraper]

    class ClassConfigModel(BaseModel):
        doc_loading_provider: str = "generic_web_scraper"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_names: list
    list_of_class_ui_names: list
    list_of_class_instances: list[Any]

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

    def load(self, data_source, doc_loading_provider=None):
        provider = self.get_requested_class_instance(
            self.list_of_class_instances,
            doc_loading_provider if doc_loading_provider is not None else self.config.doc_loading_provider,
        )

        if provider:
            return provider._load(data_source.data_source_url)
        else:
            print("rnr")

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            components["doc_loading_provider"] = gr.Dropdown(
                value=GradioHelper.get_class_ui_name_from_str(
                    self.list_of_class_instances, self.config.doc_loading_provider
                ),
                choices=GradioHelper.get_list_of_class_ui_names(self.list_of_class_instances),
                label="Source Type",
                container=True,
            )
            for provider_instance in self.list_of_class_instances:
                provider_instance.create_settings_ui()

            GradioHelper.create_settings_event_listener(self.config, components)

        return components
