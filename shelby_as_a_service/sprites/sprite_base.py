from typing import Any, Dict, List, Optional, Type

from app_base import AppBase, AppInstance
from modules.utils.log_service import Logger


class SpriteBase(AppBase):
    CLASS_CONFIG_TYPE: str = "services"
    SPRITE_NAME: str
    AVAILABLE_AGENTS: List[Type]

    log: Logger
    app: AppInstance
    required_secrets: Optional[List[str]] = None

    class_config_path: List[str]
    parent_config_path: List[str]

    def __init__(self):
        self.app = AppBase.get_app()

        self.parent_config_path = [AppBase.APP_CONFIG_TYPE]

        self.class_config_path = AppBase.get_config_path(
            parent_config_path=self.parent_config_path,
            class_config_type=self.CLASS_CONFIG_TYPE,
            class_name=self.SPRITE_NAME,
        )
        self.log = AppBase.get_logger(logger_name=self.SPRITE_NAME)

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
