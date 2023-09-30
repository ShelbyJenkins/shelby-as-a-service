from typing import List, Optional, Dict


class DataSourceService:
    data_source_name: Optional[str] = "base_data_source"
    data_source_description: Optional[
        str
    ] = "default for ingesting documents from url with web_sprite"
    data_source_url: Optional[str] = None
    data_source_target_type: Optional[str] = "web_sprite"
    data_source_doc_type: Optional[str] = None
    data_source_api_url_format: Optional[str] = None
    data_source_filter_url: Optional[str] = None
    data_source_database: Optional[str] = "pinecone_service"
    update_enabled: bool = False
    retrieval_enabled: bool = True
    # service_name_: str = "data_source_instance"

    def __init__(self, app, data_source_config):
        """ """
        self.app = app
        self.app.config_manager.set_config(self, data_source_config)


class DataDomainService:
    # data_source_service_ = DataSourceService
    config: Dict[str, str] = {}
    data_domain_name: Optional[str] = "base_data_domain"
    data_domain_description: Optional[str] = "default for quick use"
    data_domain_database: Optional[str] = "pinecone_service"
    data_domain_sources: List[str] = []
    update_enabled: bool = True
    retrieval_enabled: bool = True

    # service_name_: str = "data_domain_instance"

    def __init__(self, app, data_domain_config):
        """ """
        self.app = app
        self.app.config_manager.set_config(self, data_domain_config)
        data_domain_sources_config = self.config.get("data_domain_sources", [])

        data_domain_sources = []
        for data_source_config in data_domain_sources_config or [{}]:
            data_source_service = DataSourceService(app, data_source_config)
            data_domain_sources.append(data_source_service)

        setattr(self, "data_domain_sources", data_domain_sources)


class IndexService:
    default_index_database: Optional[str] = "pinecone_service"
    # data_domain_service_ = DataDomainService
    config: Dict[str, str] = {}

    def __init__(self, app):
        """ """
        self.app = app
        self.app.config_manager.setup_service_config(self)
        index_data_domains_config = self.config.get("index_data_domains", [])

        index_data_domains = []
        for data_domain_config in index_data_domains_config or [{}]:
            data_domain_service = DataDomainService(app, data_domain_config)
            index_data_domains.append(data_domain_service)

        setattr(self, "index_data_domains", index_data_domains)
