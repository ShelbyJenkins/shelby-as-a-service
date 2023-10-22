import os
from typing import Any, List, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.database.database_local_file import LocalFileStoreDatabase
from services.database.database_pinecone import PineconeDatabase


class DatabaseService(ModuleBase):
    CLASS_NAME: str = "database_service"
    CLASS_UI_NAME: str = "Databases"

    REQUIRED_CLASSES: List[Type] = [LocalFileStoreDatabase, PineconeDatabase]

    class ClassConfigModel(BaseModel):
        database_provider: str = "pinecone_database"
        retrieve_n_docs: int = 6

    config: ClassConfigModel
    list_of_class_instances: list[Any]
    list_of_class_ui_names: list

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

    def query_index(
        self,
        search_terms,
        retrieve_n_docs,
        data_domain_name,
        database_provider=None,
    ) -> list[dict]:
        if database_provider is None:
            database_provider = self.config.database_provider

        provider = self.get_requested_class_instance(
            self.list_of_class_instances,
            database_provider if database_provider is not None else self.config.database_provider,
        )

        if provider:
            return provider.query_index(
                search_terms=search_terms,
                retrieve_n_docs=self.config.retrieve_n_docs if retrieve_n_docs is None else retrieve_n_docs,
                data_domain_name=data_domain_name,
            )
        else:
            print("rnr")
            return []

    def fetch_by_ids(
        self,
        ids=None,
        retrieve_n_docs=None,
        data_domain_name=None,
        database_provider=None,
    ):
        provider = self.get_requested_class_instance(self.list_of_class_instances, database_provider)
        if provider:
            return provider.fetch_by_ids(
                ids=ids,
                retrieve_n_docs=retrieve_n_docs,
                data_domain_name=data_domain_name,
            )
        else:
            print("rnr")
            return []

    def write_documents_to_database(
        self,
        documents,
        data_domain=None,
        data_source=None,
        database_provider=None,
    ):
        provider = self.get_requested_class_instance(self.list_of_class_instances, database_provider)
        if provider:
            return provider.write_documents_to_database(documents, data_domain, data_source)
        else:
            print("rnr")

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            components["database_provider"] = gr.Dropdown(
                value=GradioHelper.get_class_ui_name_from_str(self.list_of_class_instances, self.config.database_provider),
                choices=GradioHelper.get_list_of_class_ui_names(self.list_of_class_instances),
                label="Source Type",
                container=True,
                min_width=0,
            )
            components["retrieve_n_docs"] = gr.Number(
                value=self.config.retrieve_n_docs, label="Number of Documents to Retrieve", container=True, min_width=0
            )
            for provider_instance in self.list_of_class_instances:
                provider_instance.create_settings_ui()

            GradioHelper.create_settings_event_listener(self.config, components)

        return components
