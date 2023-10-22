import os
from typing import Any, Optional, Type

from app.module_base import ModuleBase
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService


class ContextIndexBase(ModuleBase):
    CLASS_NAME: str = "context_index"

    class ClassConfigModel(BaseModel):
        database_provider: str = "pinecone_database"
        doc_loading_provider: str = "generic_web_scraper"

        class Config:
            extra = "ignore"

    local_index_dir: str
    database_service: DatabaseService

    data_domains: dict[str, Any] = {}
    list_of_data_domain_ui_names: list[str]

    @classmethod
    def setup_context_index(cls, config_file_dict: dict[str, Any] = {}):
        cls.local_index_dir = os.path.join(cls.APP_DIR_PATH, cls.app.app_name, ContextIndexBase.CLASS_NAME)

        index_config_file_dict = config_file_dict.get(cls.CLASS_NAME, {})
        cls.config = cls.ClassConfigModel(**config_file_dict)
        cls.database_service = DatabaseService(
            config_file_dict=index_config_file_dict, database_provider=cls.config.database_provider
        )

        if getattr(index_config_file_dict, "data_domains", {}) == {}:
            new_data_domain = DataDomain()
            cls.data_domains[new_data_domain.config.name] = new_data_domain
        else:
            data_domains_dict = index_config_file_dict["data_domains"]
            for domain_name, _ in data_domains_dict.items():
                cls.data_domains[domain_name] = DataDomain(config_file_dict=data_domains_dict)

    @staticmethod
    def list_context_class_names(list_of_instance):
        list_of_instance_ui_names = []
        for instance in list_of_instance:
            list_of_instance_ui_names.append(instance.NAME)
        return list_of_instance_ui_names


class DataDomain(ContextIndexBase):
    CLASS_NAME: str = "data_domain"
    REQUIRED_CLASSES: list[Type] = []

    class ClassConfigModel(BaseModel):
        name: str = "A default topic"
        description: str = "A default description"
        batch_update_enabled: bool = True

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_ui_names: list[str]
    list_of_class_instances: list[Any]

    data_sources: dict[str, Any] = {}

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

        if getattr(config_file_dict, "data_sources", {}) == {}:
            new_data_source = DataSource()
            self.data_sources[new_data_source.config.name] = new_data_source
        else:
            data_domains_dict = config_file_dict["data_sources"]
            for source_name, _ in data_domains_dict.items():
                self.data_sources[source_name] = DataSource(config_file_dict=data_domains_dict)


class DataSource(ContextIndexBase):
    CLASS_NAME: str = "data_source"
    REQUIRED_CLASSES: list[Type] = [DocLoadingService]

    class ClassConfigModel(BaseModel):
        name: str = "A default source"
        description: str = "A default description"
        doc_loading_provider: str = "generic_web_scraper"
        database_provider: str = "Local Files as a Database"
        batch_update_enabled: bool = True

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_ui_names: list[str]
    list_of_class_instances: list[Any]
    doc_loading_service: DocLoadingService

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)


class ChunkModel(BaseModel):
    pass


class DocumentModel(BaseModel):
    pass
