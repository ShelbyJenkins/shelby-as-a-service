from dataclasses import dataclass, field
from typing import List, Dict, Optional

# @dataclass
# class SourceModel:
#     source_name: Optional[str] = None
#     source_url: Optional[str] = None
#     source_type: Optional[str] = None
#     source_doc_type: Optional[str] = None
#     source_api_url_format: Optional[str] = None
#     source_filter_url: Optional[str] = None
    
# @dataclass
# class DataDomainModel:
#     data_domain_name: Optional[str] = None
#     data_domain_description: Optional[str] = None
#     data_domain_sources: Optional[Dict[str, SourceModel]]
#     data_domain_data_base: Optional[str] = None

@dataclass
class IndexModel:
    service_name_: str = 'index_service'
    index_data_domains: Optional[str] = None



