import os
from typing import Any, Optional, Type

from app.app_base import AppBase
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService


# this should load from a seperate file in the your_apps folder
class ContextIndexBase(AppBase):
    CLASS_NAME: str = "context_index"

    class ClassConfigModel(BaseModel):
        database_provider: str = "pinecone_database"
        doc_loading_provider: str = "generic_web_scraper"
        data_domains: dict[str, "DataDomain.ClassConfigModel"] = {}
        current_data_domain_name: str = "default_data_domain"
        current_data_source_name: str = "default_data_source"

        class Config:
            extra = "ignore"

    index_config: ClassConfigModel
    local_index_dir: str
    database_service: DatabaseService

    list_of_data_domain_ui_names: list[str]
    current_data_domain_instance: "DataDomain"
    current_data_source_instance: "DataSource"

    @classmethod
    def setup_context_index(cls, config_file_dict: dict[str, Any] = {}):
        cls.local_index_dir = os.path.join(cls.APP_DIR_PATH, cls.app_config.app_name, cls.CLASS_NAME)

        index_config_file_dict = config_file_dict.get(cls.CLASS_NAME, {})
        cls.index_config = ContextIndexBase.ClassConfigModel(**index_config_file_dict)

        cls.database_service = DatabaseService(
            config_file_dict=index_config_file_dict, database_provider=cls.index_config.database_provider
        )

        cls.list_of_data_domain_ui_names = []
        if cls.index_config.data_domains.get(cls.index_config.current_data_domain_name, {}) == {}:
            cls.create_data_domain(new_data_domain_name=cls.index_config.current_data_domain_name)
        for domain_name, _ in cls.index_config.data_domains.items():
            cls.list_of_data_domain_ui_names.append(domain_name)
        cls.current_data_domain_instance = DataDomain(
            domain_config=cls.index_config.data_domains[cls.index_config.current_data_domain_name]
        )

    @classmethod
    def create_data_domain(cls, new_data_domain_name: Optional[str] = None):
        if new_data_domain_name is None:
            new_data_domain_name = DataDomain.ClassConfigModel.name
        if new_data_domain_name in cls.list_of_data_domain_ui_names:
            raise Exception(f"Data domain name {new_data_domain_name} already exists")
        cls.index_config.data_domains[new_data_domain_name] = DataDomain.ClassConfigModel()
        cls.list_of_data_domain_ui_names.append(new_data_domain_name)

    @classmethod
    def create_data_source(cls, data_domain: "DataDomain", new_data_source_name: Optional[str] = None):
        if data_domain.domain_config.name not in cls.list_of_data_domain_ui_names:
            raise Exception(f"Data domain {data_domain.domain_config.name} does not exist")
        if new_data_source_name is None:
            new_data_source_name = DataSource.ClassConfigModel.name
        if new_data_source_name in data_domain.list_of_data_source_ui_names:
            raise Exception(f"Data domain name {new_data_source_name} already exists")
        data_domain.domain_config.data_sources[new_data_source_name] = DataSource.ClassConfigModel()
        data_domain.list_of_data_source_ui_names.append(new_data_source_name)

    @staticmethod
    def list_context_class_names(list_of_instance):
        list_of_instance_ui_names = []
        for instance in list_of_instance:
            list_of_instance_ui_names.append(instance.NAME)
        return list_of_instance_ui_names


class DataDomain(ContextIndexBase):
    CLASS_NAME: str = "data_domain"

    class ClassConfigModel(BaseModel):
        name: str = "default_data_domain"
        description: str = "A default description"
        data_sources: dict[str, "DataSource.ClassConfigModel"] = {}
        batch_update_enabled: bool = True

        class Config:
            extra = "ignore"

    domain_config: ClassConfigModel
    list_of_class_ui_names: list
    list_of_class_instances: list[Any]

    list_of_data_source_ui_names: list[str]

    def __init__(self, domain_config: ClassConfigModel):
        self.domain_config = domain_config
        self.list_of_data_source_ui_names = []
        if self.domain_config.data_sources.get(ContextIndexBase.index_config.current_data_source_name, {}) == {}:
            self.create_data_source(
                data_domain=self, new_data_source_name=ContextIndexBase.index_config.current_data_source_name
            )
        for source_name, _ in self.domain_config.data_sources.items():
            self.list_of_data_source_ui_names.append(source_name)
        ContextIndexBase.current_data_source_instance = DataSource(
            source_config=self.domain_config.data_sources[ContextIndexBase.index_config.current_data_source_name]
        )


class DataSource(ContextIndexBase):
    CLASS_NAME: str = "data_source"

    class ClassConfigModel(BaseModel):
        name: str = "default_data_source"
        description: str = "A default description"
        doc_loading_provider: str = "generic_web_scraper"
        database_provider: str = "Local Files as a Database"
        batch_update_enabled: bool = True

        class Config:
            extra = "ignore"

    source_config: ClassConfigModel
    list_of_class_ui_names: list
    list_of_class_instances: list[Any]

    def __init__(self, source_config):
        self.source_config = source_config


class ChunkModel(BaseModel):
    pass


class DocumentModel(BaseModel):
    pass
