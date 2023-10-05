from typing import Any, Dict, List, Optional, Type

from app_base import AppBase, AppInstance
from modules.utils.log_service import Logger
from pydantic import BaseModel, Field


class ServiceBase(AppBase):
    CLASS_CONFIG_TYPE: str = "services"
    SERVICE_NAME: str
    SERVICE_UI_NAME: str
    REQUIRED_SECRETS: Optional[List[str]] = None
    PROVIDER_TYPE: str
    DEFAULT_PROVIDER: Type
    AVAILABLE_PROVIDERS: List[Type]

    app_name: str
    log: Logger
    app: AppInstance

    parent_class: Type

    def __init__(self, parent_class=None):
        self.app = AppBase.get_app()
        if parent_class:
            self.class_config_path = AppBase.get_config_path(
                parent_config_path=parent_class.class_config_path,
                class_config_type=self.CLASS_CONFIG_TYPE,
                class_name=self.SERVICE_NAME,
            )
            self.log = parent_class.log
        else:
            self.class_config_path = None
            self.log = self.app.log

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
