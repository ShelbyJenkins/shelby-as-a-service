from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

# from modules.index.data_loaders import DataLoaders


class DataSourceDocumentModel(BaseModel):
    pass


class DataSourceModel(BaseModel):
    data_source_name: str = "default_data_source_name"
    data_source_description: str = "default_data_source_description"

    data_source_doc_type: Optional[str] = None
    data_source_api_url_format: Optional[str] = None
    data_source_filter_url: Optional[str] = None
    data_source_url: Optional[str] = None

    data_source_ingest_provider: str = "generic_web_scraper"
    data_source_database_provider: str = "local_filestore_database"
    update_enabled: bool = True
    retrieval_enabled: bool = True


class DataDomainModel(BaseModel):
    data_domain_name: str = "default_data_domain_name"
    data_domain_description: str = "data_domain_description"
    data_domain_sources: List[DataSourceModel] = [DataSourceModel()]
    data_domain_database_provider: str = "local_filestore_database"

    update_enabled: bool = True
    retrieval_enabled: bool = True


class IndexBase:
    CLASS_CONFIG_TYPE: str = "index"

    class IndexConfigModel(BaseModel):
        index_name: str = "default_index_name"
        index_data_domains: List[DataDomainModel] = [DataDomainModel()]
        default_index_database_provider: str = "local_filestore_database"

        update_enabled: bool = True
        retrieval_enabled: bool = True
