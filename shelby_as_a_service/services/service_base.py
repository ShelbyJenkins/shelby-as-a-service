from typing import Any, Dict, List, Optional, Type

from config.app_base import AppBase
from modules.utils.log_service import Logger
from services.database.database_pinecone import PineconeDatabase
from services.embedding.embedding_openai import OpenAIEmbedding
from services.llm.llm_openai import OpenAILLM


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

    available_provider_instances: List[Any]

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

        if config_provider := getattr(self.config, self.PROVIDER_TYPE, None):
            provider_instance = _find_provider(config_provider)
            if provider_instance:
                return provider_instance
        if default_provider := getattr(self.DEFAULT_PROVIDER, "PROVIDER_NAME", None):
            provider_instance = _find_provider(default_provider)
            if provider_instance:
                return provider_instance

        return None

    def instantiate_available_providers(self, service_config, **kwargs):
        available_provider_instances = []
        providers_config = service_config.get("providers", {})
        for provider in self.AVAILABLE_PROVIDERS:
            providers_config = providers_config.get(provider.PROVIDER_NAME, {})
            provider_instance = provider(providers_config=providers_config, **kwargs)
            setattr(self, provider.PROVIDER_NAME, provider_instance)
            available_provider_instances.append(provider_instance)
        return available_provider_instances

    def get_provider_names(self, default_provider):
        list_of_provider_names = []
        for provider in self.available_provider_instances:
            if provider.PROVIDER_NAME == default_provider:
                default_provider = provider.PROVIDER_UI_NAME
            list_of_provider_names.append(provider.PROVIDER_UI_NAME)
        return list_of_provider_names, default_provider
