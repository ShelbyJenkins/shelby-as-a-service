import os
import typing
from typing import Any, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.context_index.context_index_model import ContextIndexModel, DomainModel, SourceModel
from services.database.local_file import LocalFileDatabase
from services.database.pinecone import PineconeDatabase


class DatabaseService(ModuleBase):
    CLASS_NAME: str = "database_service"
    CLASS_UI_NAME: str = "Document Databases"

    REQUIRED_CLASSES: list[Type] = [LocalFileDatabase, PineconeDatabase]

    class ClassConfigModel(BaseModel):
        database_provider: str = "pinecone_database"
        retrieve_n_docs: int = 6

    config: ClassConfigModel
    list_of_class_names: list
    list_of_class_ui_names: list
    list_of_required_class_instances: list[Any]

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

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
            database_provider if database_provider is not None else self.config.database_provider,
        )

        if provider:
            return provider.query_index(
                search_terms=search_terms,
                retrieve_n_docs=self.config.retrieve_n_docs
                if retrieve_n_docs is None
                else retrieve_n_docs,
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
        provider = self.get_requested_class_instance(database_provider)
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
        provider = self.get_requested_class_instance(database_provider)
        if provider:
            return provider.write_documents_to_database(documents, data_domain, data_source)
        else:
            print("rnr")

    def create_service_management_settings_ui(self):
        ui_components = {}

        with gr.Accordion(label="Pinecone"):
            pinecone_model_instance = self.context_index.get_or_create_doc_db_instance(
                name="pinecone_database"
            )
            pinecone_database = PineconeDatabase(config_file_dict=pinecone_model_instance.config)
            ui_components[
                "pinecone_database"
            ] = pinecone_database.create_provider_management_settings_ui()

        return ui_components

    def create_service_ui_components(
        self,
        parent_instance: Union[DomainModel, SourceModel],
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in self.context_index.index.doc_dbs:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        enabled_doc_db_name = parent_instance.enabled_doc_db.name

        provider_select_dd, service_providers_dict = GradioHelpers.abstract_service_ui_components(
            service_name=self.CLASS_NAME,
            enabled_provider_name=enabled_doc_db_name,
            required_classes=self.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
