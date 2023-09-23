from models.app_base import AppBase
from models.index_model import IndexModel
from services.index.ingest_service import IngestService
from services.providers.database_service import PineconeService, LocalFileStoreService

class IndexService(AppBase):
    
    model_ = IndexModel()
    required_services_ = [PineconeService, LocalFileStoreService, IngestService]
    
    def __init__(self):
        """
        """
        super().__init__()
    

    def load_index_instance(self, index_name):
        
        pass
