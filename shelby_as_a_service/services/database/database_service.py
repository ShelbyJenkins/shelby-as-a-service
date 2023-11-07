import typing
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.context_index.context_index_model import (
    ChunkModel,
    DocumentModel,
    DomainModel,
    SourceModel,
)
from services.database.pinecone import PineconeDatabase

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class DatabaseService(ABC, ModuleBase):
    CLASS_NAME: str = "database_service"
    CLASS_UI_NAME: str = "Document Databases"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    @classmethod
    def upsert_from_source(cls, docs: list[DocumentModel], source: SourceModel):
        cls.upsert_from_provider(
            docs=docs,
            provider_name=source.enabled_doc_db.name,
            provider_config=source.enabled_doc_db.config,
        )

    @classmethod
    def query_from_provider(
        cls,
        search_terms: list[str] | str,
        provider_name: AVAILABLE_PROVIDERS_NAMES,
        provider_config: dict[str, Any] = {},
        **kwargs,
    ):
        provider: Type[DatabaseService] = cls.get_requested_class(
            requested_class=provider_name, available_classes=cls.REQUIRED_CLASSES
        )
        if isinstance(search_terms, str):
            search_terms = [search_terms]
        retrieved_docs = []
        for term in search_terms:
            docs = provider(config_file_dict=provider_config, **kwargs).query_terms(
                search_terms=term,
                **kwargs,
            )
            if docs:
                retrieved_docs.append(docs)
            else:
                cls.log.info(f"No documents found for {term}")
        return retrieved_docs

    @classmethod
    def fetch_by_ids_from_provider(
        cls,
        ids: list[int] | int,
        provider_name: AVAILABLE_PROVIDERS_NAMES,
        provider_config: dict[str, Any] = {},
        **kwargs,
    ):
        provider: Type[DatabaseService] = cls.get_requested_class(
            requested_class=provider_name, available_classes=cls.REQUIRED_CLASSES
        )
        if isinstance(ids, int):
            ids = [ids]

        docs = provider(config_file_dict=provider_config, **kwargs).fetch_by_ids(
            ids=ids,
            **kwargs,
        )
        if not docs:
            cls.log.info(f"No documents found for {id}")
        return docs

    @classmethod
    def upsert_from_provider(
        cls,
        docs,
        provider_name: AVAILABLE_PROVIDERS_NAMES,
        provider_config: dict[str, Any] = {},
        **kwargs,
    ):
        provider: Type[DatabaseService] = cls.get_requested_class(
            requested_class=provider_name, available_classes=cls.REQUIRED_CLASSES
        )

        provider(config_file_dict=provider_config, **kwargs).upsert(docs=docs, **kwargs)

    @classmethod
    def clear_existing_source_from_source(
        cls,
        source: SourceModel,
        **kwargs,
    ):
        provider: Type[DatabaseService] = cls.get_requested_class(
            requested_class=source.enabled_doc_db.name, available_classes=cls.REQUIRED_CLASSES
        )
        provider(config_file_dict=source.enabled_doc_db.config, **kwargs).clear_existing_source(
            domain_name=source.domain_model.name, source_name=source.name
        )

    @abstractmethod
    def query_terms(
        cls,
        search_terms,
        **kwargs,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_by_ids(
        cls,
        ids: list[int] | int,
        **kwargs,
    ):
        raise NotImplementedError

    @abstractmethod
    def upsert(
        cls,
        docs,
        **kwargs,
    ):
        raise NotImplementedError

    @abstractmethod
    def clear_existing_source(self, domain_name: str, source_name: str):
        raise NotImplementedError

    @classmethod
    def create_service_management_settings_ui(cls):
        ui_components = {}

        with gr.Accordion(label="Pinecone"):
            pinecone_model_instance = cls.context_index.get_or_create_doc_db_instance(
                name="pinecone_database"
            )
            pinecone_database = PineconeDatabase(config_file_dict=pinecone_model_instance.config)
            ui_components[
                "pinecone_database"
            ] = pinecone_database.create_provider_management_settings_ui()

        return ui_components

    @classmethod
    def create_service_ui_components(
        cls,
        parent_instance: Union[DomainModel, SourceModel],
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in cls.context_index.index.doc_dbs:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        enabled_doc_db_name = parent_instance.enabled_doc_db.name

        provider_select_dd, service_providers_dict = GradioHelpers.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=enabled_doc_db_name,
            required_classes=cls.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
