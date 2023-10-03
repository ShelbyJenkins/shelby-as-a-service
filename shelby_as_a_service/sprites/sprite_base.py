from typing import Any, Dict, List, Optional, Type

from app_base import AppBase, AppInstance
from modules.utils.log_service import Logger


class SpriteBase(AppBase):
    app_name: str
    log: Logger
    app: AppInstance
    required_secrets: Optional[List[str]] = None

    available_agents: List[Type]

    def __init__(self):
        self.app = AppBase.get_app()
        AppBase.setup_service_config(self)

    def get_selected_agent(self, new_agent_name=None) -> Optional[Type]:
        """Return an instance of the requested agent.
        It uses an existing instance.
        If an existing instance doesn't exit it creates one for the sprite."""
        for agent in self.available_agents:
            if agent:
                if (
                    agent.agent_ui_name == new_agent_name
                    or agent.agent_name == new_agent_name
                ):
                    if agent_instance := getattr(self, agent.agent_name, None):
                        return agent_instance
                    else:
                        new_agent = agent(self)
                        setattr(self, agent.agent_name, new_agent)
                        return new_agent

        return None
