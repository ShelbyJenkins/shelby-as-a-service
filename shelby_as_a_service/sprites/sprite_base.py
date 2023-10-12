from typing import Any, Dict, List, Optional, Type

from config.app_base import AppBase
from modules.utils.log_service import Logger


class SpriteBase(AppBase):
    SPRITE_NAME: str
    AVAILABLE_AGENTS: List[Type]

    CLASS_NAME_TYPE: str = "SPRITE_NAME"
    CLASS_CONFIG_TYPE: str = "sprites"
    CLASS_MODEL_TYPE: str = "SpriteConfigModel"
    AVAILABLE_CLASS_TYPES: List[str] = ["AVAILABLE_AGENTS"]

    log: Logger
    available_agent_instances: List[Any]

    def __init__(self):
        self.app = AppBase

        # self.log = AppBase.get_logger(logger_name=self.SPRITE_NAME)

    def get_selected_agent(self, new_agent_name=None) -> Optional[Type]:
        """Return an instance of the requested agent.
        It uses an existing instance.
        If an existing instance doesn't exit it creates one for the sprite."""
        for agent in self.AVAILABLE_AGENTS:
            if agent:
                if agent.AGENT_UI_NAME == new_agent_name or agent.AGENT_NAME == new_agent_name:
                    if agent_instance := getattr(self, agent.AGENT_NAME, None):
                        return agent_instance
                    else:
                        new_agent = agent(self)
                        setattr(self, agent.AGENT_NAME, new_agent)
                        return new_agent

        return None

    def instantiate_available_agents(self, sprite_config, **kwargs):
        available_agent_instances = []
        agents_config = sprite_config.get("agents", {})
        for agent in self.AVAILABLE_AGENTS:
            agent_config = agents_config.get(agent.AGENT_NAME, {})
            agent_instance = agent(agent_config=agent_config, **kwargs)

            setattr(self, agent.AGENT_NAME, agent_instance)
            available_agent_instances.append(agent_instance)
        return available_agent_instances
