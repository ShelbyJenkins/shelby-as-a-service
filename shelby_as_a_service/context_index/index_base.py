import os
from typing import Any, Optional, Type

from app.module_base import ModuleBase
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService


class ContextIndexBase(ModuleBase):
    CLASS_NAME: str = "context_index"

    class ContextIndexConfig(BaseModel):
        database_provider: str = "pinecone_database"
        doc_loading_provider: str = "generic_web_scraper"

        class Config:
            extra = "ignore"

    local_index_dir: str
    database_service: DatabaseService
    doc_loading_service: DocLoadingService

    data_domains: dict[str, Any] = {}
    list_of_data_domain_ui_names: list[str]

    @classmethod
    def setup_context_index(cls, config_file_dict: dict[str, Any] = {}):
        cls.local_index_dir = os.path.join(cls.APP_DIR_PATH, cls.app_config.app_name, ContextIndexBase.CLASS_NAME)

        index_config_file_dict = config_file_dict.get(cls.CLASS_NAME, {})
        cls.config = cls.ContextIndexConfig(**config_file_dict)
        cls.database_service = DatabaseService(
            config_file_dict=index_config_file_dict, database_provider=cls.config.database_provider
        )
        cls.doc_loading_service = DocLoadingService(
            config_file_dict=index_config_file_dict, database_provider=cls.config.doc_loading_provider
        )

        if getattr(index_config_file_dict, "data_domains", {}) == {}:
            new_data_domain = DataDomain()
            cls.data_domains[new_data_domain.config.name] = new_data_domain
        else:
            data_domains_dict = index_config_file_dict["data_domains"]
            for domain_name, domain_config in data_domains_dict.items():
                cls.data_domains[domain_name] = DataDomain(config_file_dict=domain_config)

        return cls

    @staticmethod
    def list_context_class_names(list_of_instance):
        list_of_instance_ui_names = []
        for instance in list_of_instance:
            list_of_instance_ui_names.append(instance.NAME)
        return list_of_instance_ui_names


class DataDomain(ContextIndexBase):
    CLASS_NAME: str = "data_domain"

    class DataDomainConfig(BaseModel):
        name: str = "A default topic"
        description: str = "A default description"
        database_provider: str = "pinecone_database"
        doc_loading_provider: str = "generic_web_scraper"
        batch_update_enabled: bool = True

        class Config:
            extra = "ignore"

    config: DataDomainConfig
    data_sources: dict[str, Any] = {}
    list_of_data_source_ui_names: list[str]

    def __init__(self, config_file_dict={}):
        self.config = self.DataDomainConfig(**config_file_dict)
        if getattr(config_file_dict, "data_sources", {}) == {}:
            new_data_source = DataSource()
            self.data_sources[new_data_source.config.name] = new_data_source
        else:
            data_domains_dict = config_file_dict["data_sources"]
            for source_name, source_config in data_domains_dict.items():
                self.data_sources[source_name] = DataSource(config_file_dict=source_config)


class DataSource(ContextIndexBase):
    CLASS_NAME: str = "data_source"

    class DataSourceConfig(BaseModel):
        name: str = "A default source"
        description: str = "A default description"
        data_source_url: Optional[str] = None

        # doc_loading_provider: str = "generic_web_scraper"
        doc_loading_provider_name: str = "generic_web_scraper"
        doc_loading_provider_config: dict[str, Any] = {}
        database_provider: str = "Local Files as a Database"
        batch_update_enabled: bool = True

        class Config:
            extra = "ignore"

    config: DataSourceConfig

    def __init__(self, config_file_dict={}):
        self.config = self.DataSourceConfig(**config_file_dict)
        for doc_loader in self.doc_loading_service.doc_loading_providers:
            if doc_loader.CLASS_NAME == self.config.doc_loading_provider_name:
                self.config.doc_loading_provider_config = doc_loader.ClassConfigModel(
                    **self.config.doc_loading_provider_config
                ).model_dump()
                break


class ChunkModel(BaseModel):
    pass


class DocumentModel(BaseModel):
    pass
