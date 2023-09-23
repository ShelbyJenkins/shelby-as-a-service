from models.index_model import IndexModel
from models.app_base import AppBase


class IndexService(AppBase):
    
    model_ = IndexModel()
    required_services_ = []
    
    def __init__(self):
        """
        """
        super().__init__()
