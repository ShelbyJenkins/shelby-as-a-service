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
    config: Type
    DEFAULT_MODEL: str

    def __init__(self):
        self.app = AppBase
        self.log = AppBase.log

    def get_model(self, requested_model_name=None):
        """Returns an instance of a model
        First tries the requested model,
        Then tries the classes's config model,
        Then tries provider class default"""
        model_instance = None
        available_models = getattr(self, "AVAILABLE_MODELS", [])
        if requested_model_name:
            for model in available_models:
                if model.MODEL_NAME == requested_model_name:
                    model_instance = model
                    break
        if model_instance is None:
            for model in available_models:
                if model.MODEL_NAME == self.config.model:
                    model_instance = model
                    break
        if model_instance is None:
            for model in available_models:
                if model.MODEL_NAME == self.DEFAULT_MODEL:
                    model_instance = model
                    break
        if model_instance is None:
            raise ValueError("model_instance must not be None in ProviderBase")
        return model_instance
