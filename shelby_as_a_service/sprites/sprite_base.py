from typing import Any, Dict, List, Optional, Type

from app.app_base import AppBase
from modules.utils.log_service import Logger


class SpriteBase(AppBase):
    SPRITE_NAME: str
    AVAILABLE_AGENTS: List[Type]

    CLASS_NAME_TYPE: str = "SPRITE_NAME"
    CLASS_CONFIG_TYPE: str = "sprites"
    CLASS_MODEL_TYPE: str = "SpriteConfigModel"
    AVAILABLE_CLASS_TYPES: List[str] = ["AVAILABLE_AGENTS"]

    log: Logger

    required_secrets: Optional[List[str]] = None

    def __init__(self):
        pass

        # self.log = AppBase.get_logger(logger_name=self.SPRITE_NAME)

    def get_selected_agent(self, new_agent_name=None) -> Optional[Type]:
        """Return an instance of the requested agent.
        It uses an existing instance.
        If an existing instance doesn't exit it creates one for the sprite."""
        for agent in self.AVAILABLE_AGENTS:
            if agent:
                if (
                    agent.AGENT_UI_NAME == new_agent_name
                    or agent.AGENT_NAME == new_agent_name
                ):
                    if agent_instance := getattr(self, agent.AGENT_NAME, None):
                        return agent_instance
                    else:
                        new_agent = agent(self)
                        setattr(self, agent.AGENT_NAME, new_agent)
                        return new_agent

        return None
