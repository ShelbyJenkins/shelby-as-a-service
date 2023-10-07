from typing import Any, Dict, List, Optional, Type

from app.app_base import AppBase
from modules.utils.log_service import Logger
from services.providers.database_pinecone import PineconeDatabase
from services.providers.embedding_openai import OpenAIEmbedding
from services.providers.llm_openai import OpenAILLM


class ServiceBase(AppBase):
    SERVICE_NAME: str
    SERVICE_UI_NAME: str
    REQUIRED_SECRETS: Optional[List[str]] = None
    PROVIDER_TYPE: str
    DEFAULT_PROVIDER: Type
    AVAILABLE_PROVIDERS: List[Type]

    CLASS_NAME_TYPE: str = "SERVICE_NAME"
    CLASS_UI_NAME_TYPE: str = "SERVICE_UI_NAME"
    CLASS_CONFIG_TYPE: str = "services"
    CLASS_MODEL_TYPE: str = "ServiceConfigModel"
    AVAILABLE_CLASS_TYPES: List[str] = ["AVAILABLE_PROVIDERS"]

    log: Logger
    openai_llm: OpenAILLM
    openai_embedding: OpenAIEmbedding
    pinecone_database: PineconeDatabase
    local_filestore_database: Any
    generic_recursive_web_scraper: Any
    generic_web_scraper: Any

    def __init__(self):
        self.app = AppBase
        self.log = AppBase.log

    def get_provider(self, new_provider_name=None):
        """Returns an instance of a provider
        First tries the requested provider,
        Then tries the parent_class's,
        Then uses default"""

        def _find_provider(check_provider_name):
            if not self.AVAILABLE_PROVIDERS:
                return None
            for provider in self.AVAILABLE_PROVIDERS:
                if (
                    provider.PROVIDER_NAME == check_provider_name
                    or provider.PROVIDER_UI_NAME == check_provider_name
                ):
                    if provider_instance := getattr(self, provider.PROVIDER_NAME, None):
                        return provider_instance
                    else:
                        new_provider = provider(self)
                        setattr(self, provider.PROVIDER_NAME, new_provider)
                        return new_provider

                return None

        # Try the requested provider
        if new_provider_name:
            provider_instance = _find_provider(new_provider_name)
            if provider_instance:
                return provider_instance
        # Then the service's agent
        if agent_provider := getattr(self.parent_class, self.PROVIDER_TYPE, None):
            provider_instance = _find_provider(agent_provider)
            if provider_instance:
                return provider_instance
        # The the service's default
        if default_provider := getattr(self.DEFAULT_PROVIDER, "PROVIDER_NAME", None):
            provider_instance = _find_provider(default_provider)
            if provider_instance:
                return provider_instance

        return None
