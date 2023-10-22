import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from app.app_base import AppBase


class ModuleBase(AppBase):
    update_settings_file: bool = False
    log: logging.Logger

    @staticmethod
    def setup_class_instance(class_instance, config_file_dict, **kwargs):
        class_name = class_instance.__class__.__name__
        class_instance.log = logging.getLogger(class_name)

        module_config_file_dict = config_file_dict.get(class_instance.CLASS_NAME, {})
        merged_config = {**kwargs, **module_config_file_dict}

        available_models = None

        if model_definitions := getattr(class_instance, "MODEL_DEFINITIONS", None):
            available_models = ModuleBase.create_model_instances(
                class_instance, model_definitions, module_config_file_dict, **kwargs
            )
            merged_config["available_models"] = available_models

        class_instance.config = class_instance.ClassConfigModel(**merged_config)

        list_of_class_instances = []
        list_of_class_ui_names = []

        if REQUIRED_CLASSES := getattr(class_instance, "REQUIRED_CLASSES", None):
            for required_module in REQUIRED_CLASSES:
                if new_class_instance := ModuleBase.create_class_instance(
                    class_instance, required_module, module_config_file_dict, **kwargs
                ):
                    list_of_class_ui_names.append(new_class_instance.CLASS_UI_NAME)
                    list_of_class_instances.append(new_class_instance)

        if extension_modules := getattr(class_instance, "extension_modules", None):
            for extension_module in extension_modules:
                if new_class_instance := ModuleBase.create_class_instance(
                    class_instance, extension_module, module_config_file_dict, **kwargs
                ):
                    list_of_class_ui_names.append(new_class_instance.CLASS_UI_NAME)
                    list_of_class_instances.append(new_class_instance)

        if ui_views := getattr(class_instance, "UI_VIEWS", None):
            class_instance.ui_view_instances = []
            for view_module in ui_views:
                if new_class_instance := ModuleBase.create_class_instance(
                    class_instance, view_module, module_config_file_dict, **kwargs
                ):
                    class_instance.ui_view_instances.append(new_class_instance)

        if providers_type := getattr(class_instance, "PROVIDERS_TYPE", None):
            setattr(class_instance, providers_type, list_of_class_instances)
        else:
            class_instance.list_of_class_instances = list_of_class_instances
        class_instance.list_of_class_ui_names = list_of_class_ui_names

        if required_secrets := getattr(class_instance, "REQUIRED_SECRETS", None):
            for required_secret in required_secrets:
                ModuleBase.set_secret(required_secret)

    @staticmethod
    def create_class_instance(parent_class_instance, new_module, module_config_file_dict={}, **kwargs):
        new_class_instance = None
        if CLASS_NAME := getattr(new_module, "CLASS_NAME", None):
            new_class_instance = new_module(module_config_file_dict, **kwargs)
            setattr(parent_class_instance, CLASS_NAME, new_class_instance)

        return new_class_instance

    @staticmethod
    def create_model_instances(parent_class_instance, model_definitions, module_config_file_dict={}, **kwargs):
        available_models = {}
        list_of_available_model_names = []
        for model_name, definition in model_definitions.items():
            model_config_file_dict = module_config_file_dict.get(model_name, {})
            new_model_instance = parent_class_instance.ModelConfig(**{**model_config_file_dict, **definition})
            list_of_available_model_names.append(model_name)
            available_models[model_name] = new_model_instance

        if models_type := getattr(parent_class_instance, "MODELS_TYPE", None):
            setattr(parent_class_instance, models_type, list_of_available_model_names)
        return available_models

    @staticmethod
    def set_secret(required_secret):
        env_secret = None
        secret_str = f"{AppBase.app.app_name}_{required_secret}".upper()
        env_secret = os.environ.get(secret_str, None)
        if env_secret:
            AppBase.secrets[required_secret] = env_secret
        else:
            print(f"Secret: {required_secret} is None!")

    @staticmethod
    def get_requested_class_instance(available_class_instances, requested_module):
        for class_instance in available_class_instances:
            if class_instance.CLASS_NAME == requested_module or class_instance.CLASS_UI_NAME == requested_module:
                return class_instance

    @staticmethod
    def get_model(provider_instance, requested_model_name=None):
        model_instance = None
        available_models = provider_instance.config.available_models
        if requested_model_name:
            for model_name, model in available_models.items():
                if model.MODEL_NAME == requested_model_name:
                    model_instance = model
                    break
        if model_instance is None:
            for model_name, model in available_models.items():
                if model.MODEL_NAME == provider_instance.config.current_model_name:
                    model_instance = model
                    break
        if model_instance is None:
            raise ValueError("model_instance must not be None in AppBase")
        return model_instance
