from typing import Dict, Optional, List
from app import AppBase


class ServiceBase(AppBase):
    embedding_provider: str = "openai_embedding"
    query_embedding_model: str = "text-embedding-ada-002"

    def __init__(self, parent_agent=None, parent_service=None):
        if parent_agent:
            self.app = parent_agent.app
            self.parent_sprite = parent_agent.parent_sprite
            self.parent_agent = parent_agent
        if parent_service:
            self.parent_sprite = parent_service.parent_agent.parent_sprite
            self.parent_agent = parent_service.parent_agent
            self.app = self.parent_agent.app
            self.parent_service = parent_service
        self.index = self.app.index
        self.log = self.app.log

    def get_provider(self, provider_type, provider_name=None):
        """Returns an instance of a provider
        First tries the requested provider,
        Then tries the parent_agent's,
        Then uses default"""
        # Tries the requested provider
        if provider_name:
            if provider_instance := getattr(self, provider_name, None):
                if provider_instance:
                    return provider_instance
        # Then the parent's agent
        if provider := getattr(self.parent_agent, provider_type, None):
            if provider_instance := getattr(self, provider, None):
                if provider_instance:
                    return provider_instance
        # Then the default
        return getattr(self, self.default_provider, None)

    def get_model(self, model_type, model_name=None):
        """Returns an instance of a model
        First tries the requested model,
        Then tries the parent_agent's,
        Then uses default"""
        # Tries the requested model
        if model_name:
            available_models = getattr(self, "available_models", [])
            model_instance = next(
                (model for model in available_models if model.model_name == model_name),
                None,
            )
            if model_instance:
                return model_instance
        # Then the parent's agent
        if model := getattr(self.parent_agent, model_type, None):
            if model_instance := getattr(self, model, None):
                return model_instance
        # Then the default
        return getattr(self, self.default_model, None)
