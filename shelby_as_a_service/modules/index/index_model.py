from typing import Any, Dict, List, Optional, Union

from app_base import AppBase
from pydantic import BaseModel

# from modules.index.data_loaders import DataLoaders


class DataSourceDocumentModel(BaseModel):
    pass


class DataSourceModel(AppBase):
    data_source_name: Optional[str] = None
    data_source_description: Optional[str] = None
    data_source_doc_type: Optional[str] = None
    data_source_api_url_format: Optional[str] = None
    data_source_filter_url: Optional[str] = None

    data_source_ingest_provider: Any = None
    data_source_database_provider: Optional[str] = None
    data_source_url: Optional[str] = None
    update_enabled: bool = True
    retrieval_enabled: bool = True

    def __init__(self, data_source_config):
        """ """
        self.app = AppBase.get_app()
        self.app_name = self.app.app_name
        self.config = data_source_config
        AppBase.set_config(self, data_source_config)


class DataDomainModel(AppBase):
    data_domain_name: str
    data_domain_description: Optional[str] = None
    data_domain_database_provider: Optional[str] = None
    data_domain_sources: List[Any] = []
    update_enabled: bool = True
    retrieval_enabled: bool = True

    def __init__(self, data_domain_config):
        """ """
        self.app = AppBase.get_app()
        self.app_name = self.app.app_name
        self.config = data_domain_config
        AppBase.set_config(self, data_domain_config)

        data_domain_sources_config = self.config.get("data_domain_sources", [])

        data_domain_sources = []
        for data_source_config in data_domain_sources_config or [{}]:
            data_source_service = DataSourceModel(data_source_config)
            data_domain_sources.append(data_source_service)

        setattr(self, "data_domain_sources", data_domain_sources)


class IndexModel(AppBase):
    CLASS_CONFIG_TYPE: str = "services"
    name_model: str = "index_model"
    index_data_domains: List[DataDomainModel]
    default_index_database: Optional[str] = "pinecone_database"
    config: Dict[str, str] = {}

    def __init__(self):
        """ """
        self.app = AppBase.get_app()
        config = AppBase.get_config(self)
        AppBase.set_config(self, config)
        index_data_domains_config = self.config.get("index_data_domains", [])

        index_data_domains = []
        for data_domain_config in index_data_domains_config or [{}]:
            data_domain_service = DataDomainModel(data_domain_config)
            index_data_domains.append(data_domain_service)

        setattr(self, "index_data_domains", index_data_domains)
