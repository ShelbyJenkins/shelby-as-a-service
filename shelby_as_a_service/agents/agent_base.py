from typing import Any, Dict, List, Optional

from app_base import AppBase, AppInstance
from modules.utils.log_service import Logger


class AgentBase(AppBase):
    CLASS_CONFIG_TYPE: str = "services"
    AGENT_NAME: str
    app_name: str
    log: Logger
    app: AppInstance
    class_config_path: Optional[List[str]]

    def __init__(self, parent_class=None):
        self.app = AppBase.get_app()
        if parent_class:
            self.class_config_path = AppBase.get_config_path(
                parent_config_path=parent_class.class_config_path,
                class_config_type=self.CLASS_CONFIG_TYPE,
                class_name=self.AGENT_NAME,
            )
            self.log = parent_class.log
        else:
            self.class_config_path = None
            self.log = self.app.log
