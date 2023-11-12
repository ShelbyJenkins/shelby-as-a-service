from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from agents import AVAILABLE_AGENT_NAMES, AVAILABLE_AGENT_UI_NAMES, AVAILABLE_AGENTS
from services.service_base import ServiceBase


class AgentService(ABC, ServiceBase):
    CLASS_NAME: str = "agent_service"
    CLASS_UI_NAME: str = "Agent Service"
    AVAILABLE_AGENTS: list[Type] = AVAILABLE_AGENTS
    AVAILABLE_AGENT_UI_NAMES: list[str] = AVAILABLE_AGENT_UI_NAMES
    AVAILABLE_AGENT_NAMES = AVAILABLE_AGENT_NAMES
