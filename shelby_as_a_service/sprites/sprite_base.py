from typing import Dict, Optional, List
from modules.app_base import AppBase
from modules.utils.log_service import Logger

class SpriteBase(AppBase):
    
    service_path_: str = "services" # Change to sprites
    config_: Dict[str, str] = {}

    def __init__(self):
        
        
        
        super().__init__()
        SpriteBase.setup_sprite(self)

        
    def setup_sprite(self):
        
        # from_file overwrites class vars from file
        config = {**vars(self), **(self.config or {})}

        # Removes services object used to structure the json file
        if config.get("services", None):
            config.pop("services")

        for key, value in config.items():
            setattr(self, key, value)