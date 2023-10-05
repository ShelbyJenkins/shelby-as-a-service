from typing import Any, Dict, List, Optional

from app.app_base import AppBase
from modules.utils.log_service import Logger


class AgentBase(AppBase):
    AGENT_NAME: str
    app_name: str
    log: Logger

    CLASS_NAME_TYPE: str = "AGENT_NAME"
    CLASS_CONFIG_TYPE: str = "agents"
    CLASS_MODEL_TYPE: str = "AgentConfigModel"
    AVAILABLE_CLASS_TYPES: List[str] = ["AVAILABLE_SERVICES"]

    def __init__(self):
        pass
