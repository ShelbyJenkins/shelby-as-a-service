import os
from typing import Any, Optional, Type, Union

from app.module_base import ModuleBase
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService


class ContextIndexBase(ModuleBase):
    CLASS_NAME: str = "context_index"
    REQUIRED_CLASSES: list[Type] = [DatabaseService, DocLoadingService]

    class ClassConfigModel(BaseModel):
        database_provider: str = "pinecone_database"
        current_domain_name: str = "default_data_domain"
        data_domains: dict[str, "DataDomain.ClassConfigModel"] = {}
        doc_loading_provider: str = "generic_web_scraper"

        class Config:
            extra = "ignore"

    index_config: ClassConfigModel
    local_index_dir: str
    database_service: DatabaseService
    doc_loading_service: DocLoadingService

    list_of_data_domain_ui_names: list
    current_domain: "DataDomain"

    @classmethod
    def setup_context_index(cls, config_file_dict: dict[str, Any] = {}):
        cls.local_index_dir = os.path.join(cls.APP_DIR_PATH, cls.app_config.app_name, cls.CLASS_NAME)

        index_config_file_dict = config_file_dict.get(cls.CLASS_NAME, {})
        cls.index_config = ContextIndexBase.ClassConfigModel(**index_config_file_dict)

        cls.database_service = DatabaseService(
            config_file_dict=index_config_file_dict, database_provider=cls.index_config.database_provider
        )
        cls.doc_loading_service = DocLoadingService(
            config_file_dict=index_config_file_dict, doc_loading_provider=cls.index_config.doc_loading_provider
        )

        cls.list_of_data_domain_ui_names = []
        if cls.index_config.data_domains.get(cls.index_config.current_domain_name, {}) == {}:
            cls.create_data_domain(domain_name=cls.index_config.current_domain_name)
        for domain_name, _ in cls.index_config.data_domains.items():
            cls.list_of_data_domain_ui_names.append(domain_name)
        cls.current_domain = DataDomain(domain_config=cls.index_config.data_domains[cls.index_config.current_domain_name])

    @classmethod
    def get_requested_domain(cls, requested_domain_name: str):
        if requested_domain_name not in cls.list_of_data_domain_ui_names:
            raise Exception(f"Data domain name {requested_domain_name} does not exist")
        cls.current_domain = DataDomain(domain_config=cls.index_config.data_domains[requested_domain_name])
        cls.index_config.current_domain_name = requested_domain_name

    @classmethod
    def get_requested_source(cls, requested_source_name: str):
        if requested_source_name not in cls.current_domain.list_of_data_source_ui_names:
            raise Exception(f"Data source name {requested_source_name} does not exist")
        cls.current_domain.current_source = DataSource(
            source_config=cls.current_domain.domain_config.data_sources[requested_source_name]
        )
        cls.current_domain.domain_config.current_source_name = requested_source_name

    @classmethod
    def create_data_domain(
        cls,
        domain_name: Optional[str] = None,
        description: Optional[str] = None,
        database_provider: Optional[str] = None,
        doc_loading_provider: Optional[str] = None,
        batch_update_enabled: bool = True,
    ):
        if not description:
            description = DataDomain.ClassConfigModel.model_fields["description"].default
        if not domain_name:
            domain_name = DataDomain.ClassConfigModel.model_fields["name"].default
        counter = 1
        while domain_name in cls.list_of_data_domain_ui_names:
            domain_name = f"{domain_name}_{counter}"
            counter += 1
        if not domain_name:
            raise Exception("Data domain name cannot be None")
        cls.index_config.data_domains[domain_name] = DataDomain.ClassConfigModel(
            name=domain_name,
            description=description,
            database_provider=database_provider if database_provider is not None else cls.index_config.database_provider,
            doc_loading_provider=doc_loading_provider
            if doc_loading_provider is not None
            else cls.index_config.doc_loading_provider,
            batch_update_enabled=batch_update_enabled,
        )
        cls.list_of_data_domain_ui_names.append(domain_name)
        cls.index_config.current_domain_name = domain_name

    @classmethod
    def create_data_source(
        cls,
        data_domain: "DataDomain",
        source_name: Optional[str] = None,
        description: Optional[str] = None,
        database_provider: Optional[str] = None,
        doc_loading_provider: Optional[str] = None,
        batch_update_enabled: bool = True,
    ):
        if data_domain.domain_config.name not in cls.list_of_data_domain_ui_names:
            raise Exception(f"Data domain {data_domain.domain_config.name} does not exist")
        if not description:
            description = DataSource.ClassConfigModel.model_fields["description"].default
        if not source_name:
            source_name = DataSource.ClassConfigModel.model_fields["name"].default
        counter = 1
        while source_name in data_domain.list_of_data_source_ui_names:
            source_name = f"{source_name}_{counter}"
            counter += 1
        if not source_name:
            raise Exception("Data source name cannot be None")
        data_domain.domain_config.data_sources[source_name] = DataSource.ClassConfigModel(
            name=source_name,
            description=description,
            database_provider=database_provider
            if database_provider is not None
            else data_domain.domain_config.database_provider,
            doc_loading_provider=doc_loading_provider
            if doc_loading_provider is not None
            else data_domain.domain_config.doc_loading_provider,
            batch_update_enabled=batch_update_enabled,
        )
        data_domain.list_of_data_source_ui_names.append(source_name)
        data_domain.domain_config.current_source_name = source_name

    @classmethod
    def create_service_configs(cls, config, service):
        service_name = service.CLASS_NAME
        if (service_config := getattr(config, service_name, {})) == {}:
            service_config = {}
        for class_instance in service.list_of_class_instances:
            if service_config.get(class_instance.CLASS_NAME, {}) == {}:
                service_config[class_instance.CLASS_NAME] = {}
            service_config[class_instance.CLASS_NAME] = class_instance.config.model_dump()
        return service_config


class DataDomain(ContextIndexBase):
    CLASS_NAME: str = "data_domain"
    REQUIRED_CLASSES: list[Type] = [DatabaseService, DocLoadingService]

    class ClassConfigModel(BaseModel):
        name: Optional[str] = "default_data_domain"
        description: Optional[str] = "A default description"
        database_provider: Optional[str] = None
        doc_loading_provider: Optional[str] = None
        doc_loading_config: dict = {}
        batch_update_enabled: bool = True
        data_sources: dict[str, "DataSource.ClassConfigModel"] = {}
        current_source_name: str = "default_data_source"

        class Config:
            extra = "ignore"

    domain_config: ClassConfigModel

    list_of_data_source_ui_names: list
    current_source: "DataSource"

    def __init__(self, domain_config: ClassConfigModel):
        self.domain_config = domain_config

        self.list_of_data_source_ui_names = []
        if self.domain_config.data_sources.get(self.domain_config.current_source_name, {}) == {}:
            self.create_data_source(data_domain=self, source_name=self.domain_config.current_source_name)
        for source_name, _ in self.domain_config.data_sources.items():
            self.list_of_data_source_ui_names.append(source_name)
        self.current_source = DataSource(
            source_config=self.domain_config.data_sources[self.domain_config.current_source_name]
        )


class DataSource(ContextIndexBase):
    CLASS_NAME: str = "data_source"
    REQUIRED_CLASSES: list[Type] = [DatabaseService, DocLoadingService]

    class ClassConfigModel(BaseModel):
        name: Optional[str] = "default_data_source"
        description: Optional[str] = "A default description"
        batch_update_enabled: bool = True
        database_provider: Optional[str] = None

        doc_loading_provider: Optional[str] = None
        doc_loading_service: Optional[dict[str, dict]] = {}

        class Config:
            extra = "ignore"

    source_config: ClassConfigModel
    database_service: DatabaseService
    doc_loading_service: DocLoadingService

    def __init__(self, source_config):
        self.source_config = source_config
        self.doc_loading_service = DocLoadingService(
            config_file_dict=self.source_config.doc_loading_service,
            doc_loading_provider=self.source_config.doc_loading_provider,
        )
        self.source_config.doc_loading_service = self.create_service_configs(self.source_config, self.doc_loading_service)


class ChunkModel(BaseModel):
    pass


class DocumentModel(BaseModel):
    pass
