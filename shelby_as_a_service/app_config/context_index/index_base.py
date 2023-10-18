from typing import Any, Optional

from pydantic import BaseModel


class ChunkModel(BaseModel):
    pass


class DocumentModel(BaseModel):
    pass


class DataSource(BaseModel):
    NAME: str = "A default source"
    DESCRIPTION: str = "A default description"
    data_source_doc_type: Optional[str] = None
    data_source_api_url_format: Optional[str] = None
    data_source_filter_url: Optional[str] = None
    data_source_url: Optional[str] = None

    data_source_ingest_provider: str = "generic_web_scraper"
    data_source_database_provider: str = "Local Files as a Database"
    update_enabled: bool = True
    retrieval_enabled: bool = True


class DataDomain(BaseModel):
    NAME: str = "A default topic"
    DESCRIPTION: str = "A default description"
    data_domain_sources: Optional[list[DataSource]] = []
    default_database_provider: str = "Local Files as a Database"

    update_enabled: bool = True
    retrieval_enabled: bool = True


class ContextIndexService:
    class TheContextIndex(BaseModel):
        NAME: str = "default_index_name"
        data_domains: Optional[list[DataDomain]] = []
        default_database_provider: str = "Local Files as a Database"

        update_enabled: bool = True

    @staticmethod
    def list_context_class_names(list_of_instance):
        list_of_instance_ui_names = []
        for instance in list_of_instance:
            list_of_instance_ui_names.append(instance.NAME)
        return list_of_instance_ui_names
