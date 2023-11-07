import logging
import os
import typing
from typing import Any, Optional

from app.app_base import AppBase
from pydantic import BaseModel


class ModuleBase(AppBase):
    CLASS_NAME: str
    CLASS_UI_NAME: str
    log: logging.Logger
    ClassConfigModel: typing.Type[BaseModel]
    ModelConfig: typing.Type[BaseModel]
    MODEL_DEFINITIONS: dict[str, Any]
    config: BaseModel
    list_of_class_names: list[str]
    list_of_class_ui_names: list[str]
    list_of_required_class_instances: list
    list_of_available_model_names: list[str]
    update_settings_file: bool = False
    log = logging.getLogger("ModuleBase")

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs) -> None:
        self.log = logging.getLogger(self.__class__.__name__)

        self.list_of_class_names = []
        self.list_of_class_ui_names = []
        self.list_of_required_class_instances = []

        if (class_config_file_dict := config_file_dict.get(self.CLASS_NAME, {})) == {}:
            class_config_file_dict = config_file_dict

        merged_config = {**kwargs, **class_config_file_dict}

        if model_definitions := getattr(self, "MODEL_DEFINITIONS", None):
            self.list_of_available_model_names = []
            available_models = ModuleBase.create_model_instances(
                self, model_definitions, class_config_file_dict, **kwargs
            )
            merged_config["available_models"] = available_models

        self.config = self.ClassConfigModel(**merged_config)

        self.set_secrets()

        if (required_classes := getattr(self, "REQUIRED_CLASSES", None)) is None:
            return
        for required_class in required_classes:
            if (class_name := getattr(required_class, "CLASS_NAME", None)) is None:
                self.log.error(f"Class name not found for {required_class}")
                continue
            new_instance: "ModuleBase" = required_class(class_config_file_dict, **kwargs)
            setattr(self, class_name, new_instance)

            self.list_of_class_names.append(new_instance.CLASS_NAME)
            self.list_of_class_ui_names.append(new_instance.CLASS_UI_NAME)
            self.list_of_required_class_instances.append(new_instance)
        from services.context_index.context_index import ContextIndex

        self.context_index: ContextIndex

    def create_model_instances(
        self,
        model_definitions: dict[str, typing.Any],
        class_config_file_dict: dict[str, typing.Any] = {},
        **kwargs,
    ) -> dict[str, BaseModel]:
        available_models = {}
        for model_name, definition in model_definitions.items():
            model_config_file_dict = class_config_file_dict.get(model_name, {})
            new_model_instance = self.ModelConfig(**{**model_config_file_dict, **definition})
            self.list_of_available_model_names.append(model_name)
            available_models[model_name] = new_model_instance

        if models_type := getattr(self, "MODELS_TYPE", None):
            setattr(self, models_type, self.list_of_available_model_names)
        return available_models

    def set_secrets(self) -> None:
        if required_secrets := getattr(self, "REQUIRED_SECRETS", None):
            for required_secret in required_secrets:
                env_secret = None
                secret_str = f"{AppBase.app_config.app_name}_{required_secret}".upper()
                env_secret = os.environ.get(secret_str, None)
                if env_secret:
                    AppBase.secrets[required_secret] = env_secret
                else:
                    print(f"Secret: {required_secret} is None!")

    def get_requested_class_instance(self, requested_class: str):
        for instance in self.list_of_required_class_instances:
            if instance.CLASS_NAME == requested_class or instance.CLASS_UI_NAME == requested_class:
                return instance
        raise ValueError(f"Requested class {requested_class} not found.")

    def get_model_instance(self, requested_model_name: str) -> Any:
        model_instance = None

        for model_name, model in self.MODEL_DEFINITIONS.items():
            if model_name == requested_model_name:
                model_instance = self.ModelConfig(**model)
                return model_instance

        raise ValueError(f"Requested model {requested_model_name} not found.")

    @staticmethod
    def get_requested_class(
        requested_class: str, available_classes: list[typing.Type["ModuleBase"]]
    ) -> Any:
        for available_class in available_classes:
            if (
                available_class.CLASS_NAME == requested_class
                or available_class.CLASS_UI_NAME == requested_class
            ):
                return available_class
        raise ValueError(f"Requested class {requested_class} not found in {available_classes}")
