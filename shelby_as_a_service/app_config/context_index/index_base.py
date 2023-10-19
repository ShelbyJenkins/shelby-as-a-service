import os
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
    data_sources: list[DataSource] = [DataSource()]
    default_database_provider: str = "Local Files as a Database"

    update_enabled: bool = True
    retrieval_enabled: bool = True


class ContextIndexService:
    MODULE_NAME: str = "context_index"

    class TheContextIndex(BaseModel):
        data_domains: list[DataDomain] = []
        default_database_provider: str = "Local Files as a Database"

        update_enabled: bool = True

        class Config:
            extra = "ignore"

    the_context_index: TheContextIndex
    local_index_dir: str

    @classmethod
    def setup_context_index(cls, app_base, config_file_dict: dict[str, Any], **kwargs):
        module_config_file_dict = config_file_dict.get(cls.MODULE_NAME, {})
        merged_config = {**kwargs, **module_config_file_dict}
        cls.the_context_index = cls.TheContextIndex(**merged_config)
        if getattr(cls.the_context_index, "data_domains", []) == []:
            cls.the_context_index.data_domains = []
            cls.the_context_index.data_domains.append(DataDomain())
        cls.local_index_dir = os.path.join(app_base.APP_DIR_PATH, app_base.app_config.app_name, "index")
        return cls.the_context_index

    @staticmethod
    def list_context_class_names(list_of_instance):
        list_of_instance_ui_names = []
        for instance in list_of_instance:
            list_of_instance_ui_names.append(instance.NAME)
        return list_of_instance_ui_names
