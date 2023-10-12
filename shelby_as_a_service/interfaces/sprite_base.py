from typing import Any, Dict, List, Optional, Type

from app_config.app_base import AppBase
from app_config.log_service import Logger


class SpriteBase(AppBase):
    SPRITE_NAME: str
    REQUIRED_MODULES: List[Type]

    CLASS_NAME_TYPE: str = "SPRITE_NAME"
    CLASS_CONFIG_TYPE: str = "sprites"
    CLASS_MODEL_TYPE: str = "SpriteConfigModel"
    AVAILABLE_CLASS_TYPES: List[str] = ["REQUIRED_MODULES"]

    log: Logger
    available_agent_instances: List[Any]

    def __init__(self):
        self.app = AppBase

        # self.log = AppBase.get_logger(logger_name=self.SPRITE_NAME)

    def get_selected_agent(self, new_agent_name=None) -> Optional[Type]:
        """Return an instance of the requested agent.
        It uses an existing instance.
        If an existing instance doesn't exit it creates one for the sprite."""
        for agent in self.REQUIRED_MODULES:
            if agent:
                if agent.AGENT_UI_NAME == new_agent_name or agent.MODULE_NAME == new_agent_name:
                    if agent_instance := getattr(self, agent.MODULE_NAME, None):
                        return agent_instance
                    else:
                        new_agent = agent(self)
                        setattr(self, agent.MODULE_NAME, new_agent)
                        return new_agent

        return None
