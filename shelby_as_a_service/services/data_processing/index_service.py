from models.index_model import IndexModel
from models.app_base import AppBase
from services.providers.data_base_service import PineconeService, LocalFileStoreService

class IndexService(AppBase):
    
    model_ = IndexModel()
    required_services_ = [PineconeService, LocalFileStoreService]
    
    def __init__(self):
        """
        """
        super().__init__()
        self.setup_config()
        self.setup_services()