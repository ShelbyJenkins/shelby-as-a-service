from typing import Any, Dict, List, Optional

from app_base import AppBase
from modules.utils.log_service import Logger


class SpriteBase(AppBase):
    available_agents: List[Any] = []
    agent_name: Optional[str] = None
    app_name: Optional[str] = None

    def __init__(self):
        self.app = AppBase.get_app()
        AppBase.setup_service_config(self)
        self.log = Logger(
            self.app_name,
            self.app_name,
            f"{self.app_name}.md",
            level="INFO",
        )

    def get_selected_agent(self, new_agent_name=None):
        for agent in self.available_agents:
            if agent.ui_name == new_agent_name or agent.agent_name == new_agent_name:
                return agent(self)

        return None
