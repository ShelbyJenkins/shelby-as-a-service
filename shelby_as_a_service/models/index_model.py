from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SourceModel:
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    source_doc_type: Optional[str] = None
    source_api_url_format: Optional[str] = None
    source_filter_url: Optional[str] = None
    

@dataclass
class DataDomainModel:
    data_domain_name: Optional[str] = None
    data_domain_description: Optional[str] = None
    data_domain_data_base: Optional[str] = None
    data_domain_sources: List[SourceModel] = field(default_factory=lambda: [SourceModel()])

@dataclass
class IndexModel:
    
    service_name_: str = 'index_service'
    required_variables_: List[str] = field(default_factory=list) 
    required_secrets_: List[str] = field(default_factory=list) 
    
    index_data_domains: List[DataDomainModel] = field(default_factory=lambda: [DataDomainModel()])


