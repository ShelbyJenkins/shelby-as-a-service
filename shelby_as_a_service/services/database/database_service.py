import os
from typing import Any, List, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
import services.text_processing.text as TextProcess
from app_config.app_base import AppBase
from interfaces.webui.gradio_ui import GradioUI
from pydantic import BaseModel
from services.database.database_pinecone import PineconeDatabase
from services.provider_base import ProviderBase


class LocalFileStoreDatabase(ProviderBase):
    MODULE_NAME: str = "local_filestore_database"
    MODULE_UI_NAME: str = "local_filestore_database"
    REQUIRED_SECRETS: List[str] = []

    class ModuleConfigModel(BaseModel):
        max_response_tokens: int = 1

    config: ModuleConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        module_config_file_dict = config_file_dict.get(self.MODULE_NAME, {})
        self.config = self.ModuleConfigModel(**{**kwargs, **module_config_file_dict})

    def _write_documents_to_database(self, documents, data_domain, data_source):
        data_domain_name_file_path = os.path.join(
            self.local_index_dir,
            "outputs",
            data_domain.data_domain_name,
        )
        os.makedirs(data_domain_name_file_path, exist_ok=True)
        for document in documents:
            title = TextProcess.extract_and_clean_title(document, data_source.data_source_url)
            valid_filename = "".join(c if c.isalnum() else "_" for c in title)
            file_path = os.path.join(data_domain_name_file_path, f"{valid_filename}.md")
            page_content = document.page_content
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(page_content)

            # Optionally, log the path to which the document was written
            print(f"Document written to: {file_path}")

    def create_ui(self):
        components = {}
        with gr.Accordion(label=self.MODULE_UI_NAME, open=True):
            with gr.Column():
                components["max_response_tokens"] = gr.Number(
                    value=self.config.max_response_tokens,
                    label="max_response_tokens",
                    interactive=True,
                )
            GradioUI.create_settings_event_listener(self, components)
        return components


class DatabaseService(AppBase):
    MODULE_NAME: str = "database_service"
    MODULE_UI_NAME: str = "Database Service"

    REQUIRED_MODULES: List[Type] = [LocalFileStoreDatabase, PineconeDatabase]
    AVAILABLE_PROVIDERS: List[Type] = [LocalFileStoreDatabase, PineconeDatabase]

    class ModuleConfigModel(BaseModel):
        agent_select_status_message: str = "Search index to find docs related to request."
        database_provider: str = "local_filestore_database"

    config: ModuleConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        module_config_file_dict = config_file_dict.get(self.MODULE_NAME, {})
        self.config = self.ModuleConfigModel(**{**kwargs, **module_config_file_dict})

        self.local_filestore_database = LocalFileStoreDatabase(module_config_file_dict, **kwargs)
        self.pinecone_database = PineconeDatabase(module_config_file_dict, **kwargs)

        self.database_providers = self.get_list_of_module_instances(self, self.AVAILABLE_PROVIDERS)

    def query_index(
        self,
        search_terms,
        retrieve_n_docs=None,
        data_domain_name=None,
        database_provider=None,
    ):
        provider = self.get_provider(database_provider)
        if provider:
            return provider._query_index(search_terms, retrieve_n_docs, data_domain_name)
        else:
            print("rnr")

    def write_documents_to_database(
        self,
        documents,
        data_domain,
        data_source,
    ):
        provider = self.get_provider(data_source.data_source_database_provider)
        if provider:
            return provider._write_documents_to_database(documents, data_domain, data_source)
        else:
            print("rnr")

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            components["database_provider"] = gr.Dropdown(
                value=GradioHelper.get_module_ui_name_from_str(
                    self.database_providers, self.config.database_provider
                ),
                choices=GradioHelper.get_list_of_module_ui_names(self.database_providers),
                label="Source Type",
                container=True,
            )
            for provider_instance in self.database_providers:
                provider_instance.create_ui()

            GradioUI.create_settings_event_listener(self, components)

        return components