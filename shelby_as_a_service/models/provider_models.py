from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional
class LLMs:
    gpt_4 = {"model_name": "gpt-4", "tokens_max": 8192, "cost_per_k": 0.06}

    gpt_4_32k = {"model_name": "gpt-4-32k", "tokens_max": 32768, "cost_per_k": 0.06}

    gpt_3_5 = {"model_name": "gpt-3.5-turbo", "tokens_max": 4096, "cost_per_k": 0.03}

    gpt_3_5_16k = {
        "model_name": "gpt-3.5-turbo-16k",
        "tokens_max": 16384,
        "cost_per_k": 0.03,
    }




class DataBases:
    
    @dataclass
    class LocalFileStoreServiceModel:
        index_name: Optional[str] = None
        
        service_name_: str = 'local_filestore_service'
        required_variables_: List[str] = field(default_factory=list) 
        required_secrets_: List[str] = field(default_factory=list) 
    
    @dataclass
    class PineconeServiceModel:
        pinecone_index_name: Optional[str] = None
        pinecone_index_env: str = 'us-central1-gcp'
        
        pinecone_embedding_model: str = 'text-embedding-ada-002'
        pinecone_tiktoken_encoding_model: str = 'text-embedding-ada-002'
        pinecone_embedding_max_chunk_size: int = 8191
        pinecone_embedding_batch_size: int = 100
        pinecone_vectorstore_dimension: int = 1536
        pinecone_vectorstore_upsert_batch_size: int = 20
        pinecone_vectorstore_metric: str = 'cosine'
        pinecone_vectorstore_pod_type: str = 'p1'
        pinecone_preprocessor_min_length: int = 150
        #  pinecone_text_splitter_goal_length: int = 500
        pinecone_text_splitter_goal_length: int = 750
        pinecone_text_splitter_overlap_percent: int = 15  # In percent
        pinecone_openai_timeout_seconds: float = 180.0
        
        pinecone_indexed_metadata = [
            'data_domain_name',
            'data_source_name',
            'doc_type',
            'target_type',
            'date_indexed',
        ]

        service_name_: str = 'pinecone_service'
        required_variables_: List[str] = field(default_factory=lambda: ['index_name', 'index_env'])
        required_secrets_: List[str] = field(default_factory=lambda: ['openai_api_key', 'pinecone_api_key'])
    
