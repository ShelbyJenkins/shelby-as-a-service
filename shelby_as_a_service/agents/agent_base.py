from typing import Any, Dict, List, Optional

from app.app_base import AppBase
from modules.utils.log_service import Logger
from services.database_service import DatabaseService
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService


class AgentBase(AppBase):
    AGENT_NAME: str
    CLASS_NAME_TYPE: str = "AGENT_NAME"
    CLASS_UI_NAME_TYPE: str = "AGENT_UI_NAME"
    CLASS_CONFIG_TYPE: str = "agents"
    CLASS_MODEL_TYPE: str = "AgentConfigModel"
    AVAILABLE_CLASS_TYPES: List[str] = ["AVAILABLE_SERVICES"]

    log: Logger
    llm_service: LLMService
    embedding_service: EmbeddingService
    database_service: DatabaseService
    ingest_agent: Any

    def __init__(self):
        self.app = AppBase
        self.log = AppBase.log
