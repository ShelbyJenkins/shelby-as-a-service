from typing import Dict, Optional, List
from app import AppBase
from modules.utils.log_service import Logger

class AgentBase(AppBase):
    

    def __init__(self, parent_sprite=None):
        self.app = parent_sprite.app
        self.index = self.app.index
        self.parent_sprite = parent_sprite
        self.log = self.app.log

            


        

        

        
 