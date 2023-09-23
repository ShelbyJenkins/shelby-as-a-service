from models.app_base import AppBase
from models.provider_models import DataBases

class PineconeService(AppBase):
    
    model_ = DataBases.PineconeServiceModel()
    required_services_ = None
    
    
    def __init__(self):
        super().__init__()
        self.setup_config()
        
        
        
    def delete_pinecone_index(self):
        self.log.print_and_log(f"Deleting index {self.index_name}")
        stats = self.vectorstore.describe_index_stats()
        self.log.print_and_log(stats)
        pinecone.delete_index(self.index_name)
        self.log.print_and_log(self.vectorstore.describe_index_stats())

    def clear_pinecone_index(self):
        self.log.print_and_log("Deleting all vectors in index.")
        stats = self.vectorstore.describe_index_stats()
        self.log.print_and_log(stats)
        for key in stats["namespaces"]:
            self.vectorstore.delete(deleteAll="true", namespace=key)
        self.log.print_and_log(self.vectorstore.describe_index_stats())

    def clear_pinecone_deployment(self):
        self.log.print_and_log(
            f"Clearing namespace aka deployment: {self.deployment_name}"
        )
        self.vectorstore.delete(deleteAll="true", namespace=self.deployment_name)
        self.log.print_and_log(self.vectorstore.describe_index_stats())

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
        self.log.print_and_log(log_message)

        pinecone.create_index(
            name=self.index_name,
            dimension=self.config.index_vectorstore_dimension,
            metric=self.config.index_vectorstore_metric,
            pod_type=self.config.index_vectorstore_pod_type,
            metadata_config=metadata_config,
        )
        
class LocalFileStoreService(AppBase):
    
    model_ = DataBases.LocalFileStoreServiceModel()
    required_services_ = None
    
    
    def __init__(self):
        super().__init__()
        self.setup_config()