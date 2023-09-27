from typing import List
import pinecone
from services.utils.app_base import AppBase

         
class PineconeService(AppBase):
    
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
    
    def __init__(self, config_path=None):
        super().__init__(
            service_name_="pinecone_service",
            required_variables_=["docs_to_retrieve"],
            required_secrets_=["pinecone_api_key"],
            config_path=config_path,
        )
        
        pinecone.init(
            api_key=self.secrets["pinecone_api_key"],
            environment=self.index_env,
        )
        self.pinecone_index = pinecone.Index(self.index_service.index_name)
        
    def delete_pinecone_index(self):
        print(f"Deleting index {self.index_name}")
        stats = self.vectorstore.describe_index_stats()
        print(stats)
        pinecone.delete_index(self.index_name)
        print(self.vectorstore.describe_index_stats())

    def clear_pinecone_index(self):
        print("Deleting all vectors in index.")
        stats = self.vectorstore.describe_index_stats()
        print(stats)
        for key in stats["namespaces"]:
            self.vectorstore.delete(deleteAll="true", namespace=key)
        print(self.vectorstore.describe_index_stats())

    def clear_pinecone_deployment(self):
        print(
            f"Clearing namespace aka deployment: {self.deployment_name}"
        )
        self.vectorstore.delete(deleteAll="true", namespace=self.deployment_name)
        print(self.vectorstore.describe_index_stats())

    def _clear_pinecone_data_source(self, data_source):
        data_source.vectorstore.delete(
            namespace=self.deployment_name,
            delete_all=False,
            filter={"data_source_name": {"$eq": data_source.data_source_name}},
        )

    def create_pinecone_index(self):
        metadata_config = {"indexed": self.config.index_indexed_metadata}
        # Prepare log message
        log_message = (
            f"Creating new index with the following configuration:\n"
            f" - Index Name: {self.index_name}\n"
            f" - Dimension: {self.config.index_vectorstore_dimension}\n"
            f" - Metric: {self.config.index_vectorstore_metric}\n"
            f" - Pod Type: {self.config.index_vectorstore_pod_type}\n"
            f" - Metadata Config: {metadata_config}"
        )
        # Log the message
        print(log_message)

        pinecone.create_index(
            name=self.index_name,
            dimension=self.config.index_vectorstore_dimension,
            metric=self.config.index_vectorstore_metric,
            pod_type=self.config.index_vectorstore_pod_type,
            metadata_config=metadata_config,
        )
    
    def query_index(self, dense_embedding, docs_to_retrieve, data_domain_name=None):
        # def query_vectorstore(self, dense_embedding, sparse_embedding, data_domain_name=None):

        # if data_domain_name is None:
        #     data_domain_names = []
        #     for field, _ in self.data_domains.items():
        #         data_domain_names.append(field)

        #     soft_filter = {
        #         "doc_type": {"$eq": "soft"},
        #         "data_domain_name": {"$in": data_domain_names},
        #     }

        #     hard_filter = {
        #         "doc_type": {"$eq": "hard"},
        #         "data_domain_name": {"$in": data_domain_names},
        #     }

        # else:
        #     soft_filter = {
        #         "doc_type": {"$eq": "soft"},
        #         "data_domain_name": {"$eq": data_domain_name},
        #     }
        #     hard_filter = {
        #         "doc_type": {"$eq": "hard"},
        #         "data_domain_name": {"$eq": data_domain_name},
        #     }
        

        soft_query_response = self.pinecone_index.query(
            top_k=docs_to_retrieve,
            include_values=False,
            namespace='tatum',
            include_metadata=True,
            vector=dense_embedding

        )
        # hard_query_response = self.pinecone_index.query(
        #     top_k=docs_to_retrieve,
        #     include_values=False,
        #     namespace=AppBase.app_name,
        #     include_metadata=True,
        #     filter=hard_filter,
        #     vector=dense_embedding

        # )

        # Destructures the QueryResponse object the pinecone library generates.
        returned_documents = []
        for m in soft_query_response.matches:
            response = {
                "content": m.metadata["content"],
                "title": m.metadata["title"],
                "url": m.metadata["url"],
                "doc_type": m.metadata["doc_type"],
                "score": m.score,
                "id": m.id,
            }
            returned_documents.append(response)
        # for m in hard_query_response.matches:
        #     response = {
        #         "content": m.metadata["content"],
        #         "title": m.metadata["title"],
        #         "url": m.metadata["url"],
        #         "doc_type": m.metadata["doc_type"],
        #         "score": m.score,
        #         "id": m.id,
        #     }
        #     returned_documents.append(response)

        return returned_documents
    
class LocalFileStoreService(AppBase):
    
    
    def __init__(self, config_path):
        super().__init__(
            service_name_="local_filestore_service",
            required_variables_=["docs_to_retrieve"],
            config_path=config_path,
        )
        
class DatabaseService(AppBase):
    
    default_provider: str = "pinecone_service"
    available_providers = [PineconeService, LocalFileStoreService]
    
    def __init__(self, enabled_provider=None, config_path=None):
        super().__init__(
            service_name_="database_service",
            required_variables_=["docs_to_retrieve"],
            config_path=config_path,
        )
        if enabled_provider is None:
            enabled_provider = AppBase.index_service.index_database
        self.provider = self.set_provider(enabled_provider=enabled_provider)
    