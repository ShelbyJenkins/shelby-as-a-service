from typing import Any, Dict, List, Optional, Type

from app_base import AppBase, AppInstance
from modules.utils.log_service import Logger
from pydantic import BaseModel, Field


class ProviderBase(AppBase):
    app_name: str
    log: Logger
    app: AppInstance
    required_secrets: Optional[List[str]] = None

    provider_name: str
    provider_ui_name: str

    ui_model_names: Optional[List[str]]
    type_model: Optional[str]
    available_models: Optional[List[Type]]
    default_model: Optional[str]

    def __init__(self, parent_service=None):
        self.app = AppBase.get_app()
        self.log = self.app.log
        if parent_service:
            self.parent_sprite = parent_service.parent_agent.parent_sprite
            self.parent_agent = parent_service.parent_agent
            self.parent_service = parent_service
        AppBase.setup_service_config(self)

    def get_model(self, type_model, model_name=None):
        """Returns an instance of a model
        First tries the requested model,
        Then tries the parent_agent's,
        Then uses default"""
        # Tries the requested model
        available_models = getattr(self, "available_models", [])
        if model_name:
            model_instance = next(
                (model for model in available_models if model.model_name == model_name),
                None,
            )
            if model_instance:
                return model_instance
        # Then the parent's agent
        if model := getattr(self.parent_agent, type_model, None):
            if model_instance := getattr(self, model, None):
                return model_instance
        # Then the default
        return next(
            (
                model
                for model in available_models
                if model.model_name == self.default_model
            ),
            None,
        )
