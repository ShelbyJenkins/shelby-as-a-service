from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DatabaseServiceModel:
    
    
    service_name_: str = 'database_service'
    required_variables_: List[str] = field(default_factory=list) 
    required_secrets_: List[str] = field(default_factory=list) 
    
@dataclass
class LocalFileStoreServiceModel:
    
    service_name_: str = 'local_filestore_service'
    required_variables_: List[str] = field(default_factory=list) 
    required_secrets_: List[str] = field(default_factory=list) 

@dataclass
class PineconeServiceModel:
    
    index_env: str = 'us-central1-gcp'
    
    embedding_max_chunk_size: int = 8191
    embedding_batch_size: int = 100
    vectorstore_dimension: int = 1536
    vectorstore_upsert_batch_size: int = 20
    vectorstore_metric: str = 'cosine'
    vectorstore_pod_type: str = 'p1'
    preprocessor_min_length: int = 150
    #  text_splitter_goal_length: int = 500
    text_splitter_goal_length: int = 750
    text_splitter_overlap_percent: int = 15  # In percent
    
    indexed_metadata = [
        'data_domain_name',
        'data_source_name',
        'doc_type',
        'target_type',
        'date_indexed',
    ]

    service_name_: str = 'pinecone_service'
    required_variables_: List[str] = field(default_factory=lambda: ['index_env'])
    required_secrets_: List[str] = field(default_factory=lambda: ['pinecone_api_key'])