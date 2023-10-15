from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

# from modules.index.data_loaders import DataLoaders


class ChunkModel(BaseModel):
    pass


class DocumentModel(BaseModel):
    pass


class DataSource(BaseModel):
    data_source_name: str = "default_data_source"
    data_source_ui_name: str = "default data source template"
    data_source_description: str = "default_data_source_description"

    data_source_doc_type: Optional[str] = None
    data_source_api_url_format: Optional[str] = None
    data_source_filter_url: Optional[str] = None
    data_source_url: Optional[str] = None

    data_source_ingest_provider: str = "generic_web_scraper"
    data_source_database_provider: str = "local_filestore_database"
    update_enabled: bool = True
    retrieval_enabled: bool = True


class DataDomain(BaseModel):
    data_domain_name: str = "default_data_domain"
    data_domain_ui_name: str = "default index topic"
    data_domain_description: str = "data_domain_description"
    data_domain_sources: List[DataSource] = [DataSource()]
    data_domain_database_provider: str = "local_filestore_database"

    update_enabled: bool = True
    retrieval_enabled: bool = True


class ContextIndexService:
    class TheContextIndex(BaseModel):
        index_name: str = "default_index_name"
        index_data_domains: List[DataDomain] = [DataDomain()]
        default_index_database_provider: str = "local_filestore_database"

        update_enabled: bool = True
