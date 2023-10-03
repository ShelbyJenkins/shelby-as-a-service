from typing import Any, Dict, List, Optional, Type

from app_base import AppBase, AppInstance
from modules.utils.log_service import Logger
from pydantic import BaseModel, Field


class ServiceBase(AppBase):
    app_name: str
    log: Logger
    app: AppInstance
    required_secrets: Optional[List[str]] = None

    service_name: str
    service_ui_name: str

    provider_type: str
    available_providers: List[Type]
    default_provider: Type

    def __init__(self, parent_agent=None, parent_service=None):
        self.app = AppBase.get_app()
        self.log = self.app.log
        if parent_agent:
            self.parent_sprite = parent_agent.parent_sprite
            self.parent_agent = parent_agent
        if parent_service:
            self.parent_sprite = parent_service.parent_agent.parent_sprite
            self.parent_agent = parent_service.parent_agent
            self.parent_service = parent_service
        AppBase.setup_service_config(self)

    def get_provider(self, new_provider_name=None):
        """Returns an instance of a provider
        First tries the requested provider,
        Then tries the parent_agent's,
        Then uses default"""

        def _find_provider(check_provider_name):
            if not self.available_providers:
                return None
            for provider in self.available_providers:
                if (
                    provider.provider_name == check_provider_name
                    or provider.provider_ui_name == check_provider_name
                ):
                    if provider_instance := getattr(self, provider.provider_name, None):
                        return provider_instance
                    else:
                        new_provider = provider(self)
                        setattr(self, provider.provider_name, new_provider)
                        return new_provider

                return None

        # Try the requested provider
        if new_provider_name:
            provider_instance = _find_provider(new_provider_name)
            if provider_instance:
                return provider_instance
        # Then the service's agent
        if agent_provider := getattr(self.parent_agent, self.provider_type, None):
            provider_instance = _find_provider(agent_provider)
            if provider_instance:
                return provider_instance
        # The the service's default
        if default_provider := getattr(self.default_provider, "provider_name", None):
            provider_instance = _find_provider(default_provider)
            if provider_instance:
                return provider_instance

        return None
