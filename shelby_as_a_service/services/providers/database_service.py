import pinecone
from models.app_base import AppBase
from models.database_models import DatabaseServiceModel, LocalFileStoreServiceModel, PineconeServiceModel

class PineconeService(AppBase):
    
    model_ = PineconeServiceModel()
    required_services_ = None
    index = None
    
    def __init__(self, config, sprite_name):
        super().__init__()
        self.setup_config(config, sprite_name)
        
    def initialize_pinecone(self):
        
        pinecone.init(
            api_key=self.secrets["pinecone_api_key"],
            environment=self.index_env,
        )
        self.index = pinecone.Index(self.index_service.index_name)
        
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
        

        soft_query_response = self.index.query(
            top_k=docs_to_retrieve,
            include_values=False,
            namespace='tatum',
            include_metadata=True,
            vector=dense_embedding

        )
        # hard_query_response = self.index.query(
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
    
    model_ = LocalFileStoreServiceModel()
    required_services_ = None
    

    def __init__(self, config, sprite_name):
        super().__init__()
        self.setup_config(config, sprite_name)
        
class DatabaseService(AppBase):
    
    model_ = DatabaseServiceModel()
    required_services_ = [LocalFileStoreService, PineconeService]
    
    pinecone_service = None
    local_filestore_service = None

    def __init__(self, config, sprite_name):
        super().__init__()
        self.setup_config(config, sprite_name)
        
    def initialize_database(self):
        match AppBase.index_service.index_database:
                case 'pinecone_service':
                    self.pinecone_service.initialize_pinecone()
                    return self.pinecone_service
                case 'local_filestore_service':
                    return self.local_filestore_service
                case _:
                    return None