import os
from typing import Any, List, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.module_base import ModuleBase
from pydantic import BaseModel
from services.database.database_local_file import LocalFileStoreDatabase
from services.database.database_pinecone import PineconeDatabase


class DatabaseService(ModuleBase):
    MODULE_NAME: str = "database_service"
    MODULE_UI_NAME: str = "Database Service"
    PROVIDERS_TYPE: str = "database_providers"

    REQUIRED_MODULES: List[Type] = [LocalFileStoreDatabase, PineconeDatabase]
    UI_MODULES: List[Type] = [LocalFileStoreDatabase, PineconeDatabase]

    class ModuleConfigModel(BaseModel):
        database_provider: str = "local_filestore_database"

    config: ModuleConfigModel
    database_providers: List[Any]

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

    def query_index(
        self,
        search_terms=None,
        retrieve_n_docs=None,
        data_domain_name=None,
        database_provider=None,
    ):
        provider = self.get_requested_module_instance(self.database_providers, database_provider)
        if provider:
            return provider._query_index(
                search_terms=search_terms,
                retrieve_n_docs=retrieve_n_docs,
                data_domain_name=data_domain_name,
            )
        else:
            print("rnr")

    def fetch_by_ids(
        self,
        ids=None,
        retrieve_n_docs=None,
        data_domain_name=None,
        database_provider=None,
    ):
        provider = self.get_requested_module_instance(self.database_providers, database_provider)
        if provider:
            return provider.fetch_by_ids(
                ids=ids,
                retrieve_n_docs=retrieve_n_docs,
                data_domain_name=data_domain_name,
            )
        else:
            print("rnr")

    def write_documents_to_database(
        self,
        documents,
        data_domain=None,
        data_source=None,
        database_provider=None,
    ):
        provider = self.get_requested_module_instance(self.database_providers, database_provider)
        if provider:
            return provider.write_documents_to_database(documents, data_domain, data_source)
        else:
            print("rnr")

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            components["database_provider"] = gr.Dropdown(
                value=GradioHelper.get_module_ui_name_from_str(self.database_providers, self.config.database_provider),
                choices=GradioHelper.get_list_of_module_ui_names(self.database_providers),
                label="Source Type",
                container=True,
            )
            for provider_instance in self.database_providers:
                provider_instance.create_settings_ui()

            GradioHelper.create_settings_event_listener(self, components)

        return components
