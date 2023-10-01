from typing import List, Optional, Dict, Union, Any
import modules.utils.config_manager as ConfigManager
from pydantic import BaseModel

# from modules.index.data_loaders import DataLoaders


class DataSourceDocumentModel(BaseModel):
    pass  # Maybe?


class DataSourceModel(BaseModel):
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

    # def __init__(self):
    #     """ """

    #     self.app = app
    #     ConfigManager.setup_service_config(self)


class DataDomainModel(BaseModel):
    data_domain_name: Optional[str] = None
    data_domain_description: Optional[str] = None
    data_domain_database_provider: Optional[str] = None
    data_domain_sources: List[Any] = []
    update_enabled: bool = True
    retrieval_enabled: bool = True

    # def __init__(self):
    #     """ """

    #     self.app = app
    #     ConfigManager.setup_service_config(self)
    #     data_domain_sources_config = self.config.get("data_domain_sources", [])

    #     data_domain_sources = []
    #     for data_source_config in data_domain_sources_config or [{}]:
    #         data_source_service = DataSourceModel(app, data_source_config)
    #         data_domain_sources.append(data_source_service)

    #     setattr(self, "data_domain_sources", data_domain_sources)


class IndexModel:
    default_index_database: Optional[str] = "pinecone_database"
    # data_domain_service_ = DataDomainService
    config: Dict[str, str] = {}

    def __init__(self, app):
        """ """
        self.app = app
        ConfigManager.setup_service_config(self)
        index_data_domains_config = self.config.get("index_data_domains", [])

        # index_data_domains = []
        # for data_domain_config in index_data_domains_config or [{}]:
        #     data_domain_service = DataDomainModel(app, data_domain_config)
        #     index_data_domains.append(data_domain_service)

        # setattr(self, "index_data_domains", index_data_domains)
