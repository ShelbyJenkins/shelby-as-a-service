from services.utils.app_base import AppBase
from typing import List, Optional
from services.utils.app_management import AppManager

class DataSourceService(AppBase):
    
    data_source_name: Optional[str] = 'base_data_source'
    data_source_description: Optional[str] = 'default for ingesting documents from url with local_sprite'
    data_source_url: Optional[str] = None
    data_source_target_type: Optional[str] = 'local_sprite_web'
    data_source_doc_type: Optional[str] = None
    data_source_api_url_format: Optional[str] = None
    data_source_filter_url: Optional[str] = None
    data_source_database: Optional[str] = 'pinecone_service'
    update_enabled: bool = False
    retrieval_enabled: bool = True
    service_name_="data_source_instance"

    def __init__(self, config):
        """ """
        AppBase.setup_service_from_config(self, config)

class DataDomainService(AppBase):
    
    data_source_service_ = DataSourceService
    
    data_domain_name: Optional[str] = 'base_data_domain'
    data_domain_description: Optional[str] = 'default for quick use'
    data_domain_database: Optional[str] = 'pinecone_service'
    data_domain_sources: List[str] = []
    update_enabled: bool = True
    retrieval_enabled: bool = True
    
    service_name_ = "data_domain_instance"
    
    def __init__(self, config):
        """ """
        AppBase.setup_service_from_config(self, config)
        data_domain_sources_config = config.get(
            "data_domain_sources", []
        )
        
        data_domain_sources = []
        for data_source_config in data_domain_sources_config or [{}]:
            data_source_service = DataSourceService(data_source_config)
            data_domain_sources.append(data_source_service)

        setattr(self, "data_domain_sources", data_domain_sources)

class IndexService(AppBase):
    
    index_name: Optional[str] = None
    index_database: Optional[str] = 'pinecone_service'
    data_domain_service_ = DataDomainService
    
    def __init__(self, config_path):
        """ """
        super().__init__(
            service_name_="index_service",
            required_variables_=['index_name'],
            config_path=config_path,
        )
        
        index_data_domains_config = (self.config.get("index_data_domains", []))

        index_data_domains = []
        for data_domain_config in index_data_domains_config or [{}]:
            data_domain_service = DataDomainService(data_domain_config)
            index_data_domains.append(data_domain_service)

        setattr(self, "index_data_domains", index_data_domains)

