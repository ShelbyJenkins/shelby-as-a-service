from models.app_base import AppBase
from models.provider_models import DataBases

class PineconeService(AppBase):
    
    model_ = DataBases.PineconeServiceModel()
    required_services_ = None
    
    
    def __init__(self):
        super().__init__()
        self.setup_config()
        
class LocalFileStoreService(AppBase):
    
    model_ = DataBases.LocalFileStoreServiceModel()
    required_services_ = None
    
    
    def __init__(self):
        super().__init__()
        self.setup_config()