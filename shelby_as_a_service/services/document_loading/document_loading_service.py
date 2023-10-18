from typing import Any, Iterator, List, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.module_base import ModuleBase
from interfaces.webui.gradio_ui import GradioUI
from pydantic import BaseModel, Field
from services.document_loading.document_loading_providers import GenericRecursiveWebScraper, GenericWebScraper


class DocLoadingService(ModuleBase):
    MODULE_NAME: str = "doc_loading_service"
    MODULE_UI_NAME: str = "Document Loading Service"
    REQUIRED_MODULES: List[Type] = [GenericWebScraper]

    class ModuleConfigModel(BaseModel):
        doc_loading_provider: str = "generic_web_scraper"

        class Config:
            extra = "ignore"

    config: ModuleConfigModel
    doc_loading_providers: List[Any]

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

    def load(self, data_source, doc_loading_provider=None):
        provider = self.get_requested_module_instance(self.doc_loading_providers, doc_loading_provider)
        if provider:
            return provider._load(data_source.data_source_url)
        else:
            print("rnr")

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            components["doc_loading_provider"] = gr.Dropdown(
                value=GradioHelper.get_module_ui_name_from_str(self.doc_loading_providers, self.config.doc_loading_provider),
                choices=GradioHelper.get_list_of_module_ui_names(self.doc_loading_providers),
                label="Source Type",
                container=True,
            )
            for provider_instance in self.doc_loading_providers:
                provider_instance.create_settings_ui()

            GradioHelper.create_settings_event_listener(self.config, components)

        return components
