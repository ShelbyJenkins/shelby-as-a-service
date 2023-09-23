from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DataSourceModel:
    
    data_source_name: Optional[str] = 'base_data_source'
    data_source_description: Optional[str] = 'default for ingesting documents from url with local_sprite'
    data_source_url: Optional[str] = None
    data_source_target_type: Optional[str] = 'local_sprite_web'
    data_source_doc_type: Optional[str] = None
    data_source_api_url_format: Optional[str] = None
    data_source_update_enabled: bool = True
    data_source_filter_url: Optional[str] = None
    
    service_name_: str = 'data_source_instance'

@dataclass
class DataDomainModel:
    
    data_domain_name: Optional[str] = 'base_data_domain'
    data_domain_description: Optional[str] = 'default for quick use'
    data_domain_data_base: Optional[str] = None
    data_domain_update_enabled: bool = True
    data_domain_sources: List[DataSourceModel] = field(default_factory=lambda: [DataSourceModel()])
    
    service_name_: str = 'data_domain_instance'
    
@dataclass
class IndexInstanceModel:
    
    index_name: Optional[str] = 'base_index'
    index_data_domains: List[DataDomainModel] = field(default_factory=lambda: [DataDomainModel()])
    
    service_name_: str = 'index_instance'

@dataclass
class IndexModel:
    
    index_instances: List[IndexInstanceModel] = field(default_factory=lambda: [IndexInstanceModel()])
    
    service_name_: str = 'index_service'
    required_variables_: List[str] = field(default_factory=list) 
    required_secrets_: List[str] = field(default_factory=list) 
    


