from typing import Any, Dict, List, Optional

from app_base import AppBase
from modules.utils.log_service import Logger


class AgentBase(AppBase):
    def __init__(self, parent_sprite=None):
        self.parent_sprite = parent_sprite
        self.app = AppBase.get_app()
        self.log = self.app.log
        AppBase.setup_service_config(self)
