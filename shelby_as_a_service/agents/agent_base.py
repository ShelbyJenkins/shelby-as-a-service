from typing import Dict, Optional, List
from modules.utils.log_service import Logger
from pydantic import BaseModel


class AgentBase:
    def __init__(self, parent_sprite):
        self.app = parent_sprite.app
        self.index = self.app.index
        self.parent_sprite = parent_sprite
        self.log = self.app.log
        self.app_name = self.app.app_name
