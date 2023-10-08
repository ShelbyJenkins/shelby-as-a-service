from typing import Any, Dict, List, Optional, Type

from app.app_base import AppBase
from modules.utils.log_service import Logger


class ProviderBase(AppBase):
    CLASS_NAME_TYPE: str = "PROVIDER_NAME"
    CLASS_UI_NAME_TYPE: str = "PROVIDER_UI_NAME"
    CLASS_CONFIG_TYPE: str = "providers"
    CLASS_MODEL_TYPE: str = "ProviderConfigModel"

    app_name: str
    log: Logger

    def __init__(self):
        self.app = AppBase
        self.log = AppBase.log

    def get_model(self, type_model, model_name=None):
        """Returns an instance of a model
        First tries the requested model,
        Then tries the parent_agent's,
        Then uses default"""
        # Tries the requested model
        available_models = getattr(self, "AVAILABLE_MODELS", [])
        if model_name:
            model_instance = next(
                (model for model in available_models if model.MODEL_NAME == model_name),
                None,
            )
            if model_instance:
                return model_instance
        # Then the parent's agent
        # if model := getattr(self.parent_class, type_model, None):
        #     if model_instance := getattr(self, model, None):
        #         return model_instance
        # Then the default
        return next(
            (
                model
                for model in available_models
                if model.MODEL_NAME == self.DEFAULT_MODEL
            ),
            None,
        )
