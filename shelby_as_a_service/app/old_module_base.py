import logging
import os
import typing
from typing import Any, Optional, Type

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
    REQUIRED_CLASSES: list[Type["ModuleBase"]] = []

    def __init__(self, config: dict[str, Any] = {}, **kwargs) -> None:
        self.log = logging.getLogger(self.__class__.__name__)

        self.list_of_class_names = []
        self.list_of_class_ui_names = []
        self.list_of_required_class_instances = []

        if (class_config := config.get(self.CLASS_NAME, {})) == {}:
            class_config = config

        merged_config = {**kwargs, **class_config}

        if model_definitions := getattr(self, "MODEL_DEFINITIONS", None):
            self.list_of_available_model_names = []
            available_models = ModuleBase.create_model_instances(
                self, model_definitions, class_config, **kwargs
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
            new_instance: "ModuleBase" = required_class(class_config, **kwargs)
            setattr(self, class_name, new_instance)

            self.list_of_class_names.append(new_instance.CLASS_NAME)
            self.list_of_class_ui_names.append(new_instance.CLASS_UI_NAME)
            self.list_of_required_class_instances.append(new_instance)
        from services.context_index.context_index import DocIndex

        self.doc_index: DocIndex

    def create_model_instances(
        self,
        model_definitions: dict[str, Any],
        class_config: dict[str, Any] = {},
        **kwargs,
    ) -> dict[str, BaseModel]:
        available_models = {}
        for model_name, definition in model_definitions.items():
            model_config = class_config.get(model_name, {})
            new_model_instance = self.ModelConfig(**{**model_config, **definition})
            self.list_of_available_model_names.append(model_name)
            available_models[model_name] = new_model_instance

        if models_type := getattr(self, "MODELS_TYPE", None):
            setattr(self, models_type, self.list_of_available_model_names)
        return available_models

    def get_model_instance(self, requested_model_name: str) -> Any:
        model_instance = None

        for model_name, model in self.MODEL_DEFINITIONS.items():
            if model_name == requested_model_name:
                model_instance = self.ModelConfig(**model)
                return model_instance

        raise ValueError(f"Requested model {requested_model_name} not found.")
