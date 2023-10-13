from typing import Any, Iterator, List, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.app_base import AppBase
from interfaces.webui.gradio_ui import GradioUI
from pydantic import BaseModel, Field
from services.document_loading.document_loading_providers import (
    GenericRecursiveWebScraper,
    GenericWebScraper,
)


class DocLoadingService(AppBase):
    MODULE_NAME: str = "doc_loading_service"
    MODULE_UI_NAME: str = "Document Loading Service"
    REQUIRED_MODULES: List[Type] = [GenericWebScraper]
    AVAILABLE_PROVIDERS: List[Type] = [
        GenericWebScraper,
        GenericRecursiveWebScraper,
        # OpenAPILoader,
        # LoadTextFromFile,
    ]

    class ModuleConfigModel(BaseModel):
        doc_loading_provider: str = "generic_web_scraper"

        class Config:
            extra = "ignore"

    config: ModuleConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        module_config_file_dict = config_file_dict.get(self.MODULE_NAME, {})
        self.config = self.ModuleConfigModel(**{**kwargs, **module_config_file_dict})

        self.generic_web_scraper = GenericWebScraper(module_config_file_dict, **kwargs)
        self.generic_recursive_web_scraper = GenericRecursiveWebScraper(
            module_config_file_dict, **kwargs
        )

        self.doc_loading_providers = self.get_list_of_module_instances(
            self, self.AVAILABLE_PROVIDERS
        )

    def load(self, data_source, doc_loading_provider=None):
        provider = self.get_requested_module_instance(
            self.doc_loading_providers, doc_loading_provider
        )
        if provider:
            return provider._load(data_source.data_source_url)
        else:
            print("rnr")

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            components["doc_loading_provider"] = gr.Dropdown(
                value=GradioHelper.get_module_ui_name_from_str(
                    self.doc_loading_providers, self.config.doc_loading_provider
                ),
                choices=GradioHelper.get_list_of_module_ui_names(self.doc_loading_providers),
                label="Source Type",
                container=True,
            )
            for provider_instance in self.doc_loading_providers:
                provider_instance.create_ui()

            GradioUI.create_settings_event_listener(self, components)

        return components
