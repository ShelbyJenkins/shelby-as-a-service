import os
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from app_config.app_base import AppBase


class ModuleBase(AppBase):
    update_settings_file: bool = False

    @staticmethod
    def setup_module_instance(module_instance, config_file_dict, **kwargs):
        module_config_file_dict = config_file_dict.get(module_instance.MODULE_NAME, {})
        merged_config = {**kwargs, **module_config_file_dict}

        available_models = None

        if model_definitions := getattr(module_instance, "MODEL_DEFINITIONS", None):
            available_models = ModuleBase.create_model_instances(
                module_instance, model_definitions, module_config_file_dict, **kwargs
            )
            merged_config["available_models"] = available_models

        module_instance.config = module_instance.ModuleConfigModel(**merged_config)

        list_of_module_instances = []
        list_of_module_ui_names = []

        if required_modules := getattr(module_instance, "REQUIRED_MODULES", None):
            for required_module in required_modules:
                if new_module_instance := ModuleBase.create_module_instance(
                    module_instance, required_module, module_config_file_dict, **kwargs
                ):
                    list_of_module_ui_names.append(new_module_instance.MODULE_UI_NAME)
                    list_of_module_instances.append(new_module_instance)

        if extension_modules := getattr(module_instance, "extension_modules", None):
            for extension_module in extension_modules:
                if new_module_instance := ModuleBase.create_module_instance(
                    module_instance, extension_module, module_config_file_dict, **kwargs
                ):
                    list_of_module_ui_names.append(new_module_instance.MODULE_UI_NAME)
                    list_of_module_instances.append(new_module_instance)

        if ui_views := getattr(module_instance, "UI_VIEWS", None):
            module_instance.ui_view_instances = []
            for view_module in ui_views:
                if new_module_instance := ModuleBase.create_module_instance(
                    module_instance, view_module, module_config_file_dict, **kwargs
                ):
                    module_instance.ui_view_instances.append(new_module_instance)

        if providers_type := getattr(module_instance, "PROVIDERS_TYPE", None):
            setattr(module_instance, providers_type, list_of_module_instances)
        else:
            module_instance.list_of_module_instances = list_of_module_instances
        module_instance.list_of_module_ui_names = list_of_module_ui_names

        if required_secrets := getattr(module_instance, "REQUIRED_SECRETS", None):
            for required_secret in required_secrets:
                ModuleBase.set_secret(required_secret)

    @staticmethod
    def create_module_instance(parent_module_instance, new_module, module_config_file_dict={}, **kwargs):
        new_module_instance = None
        if module_name := getattr(new_module, "MODULE_NAME", None):
            new_module_instance = new_module(module_config_file_dict, **kwargs)
            setattr(parent_module_instance, module_name, new_module_instance)

        return new_module_instance

    @staticmethod
    def create_model_instances(parent_module_instance, model_definitions, module_config_file_dict={}, **kwargs):
        available_models = {}
        list_of_available_model_names = []
        for model_name, definition in model_definitions.items():
            model_config_file_dict = module_config_file_dict.get(model_name, {})
            new_model_instance = parent_module_instance.ModelConfig(**{**model_config_file_dict, **definition})
            list_of_available_model_names.append(model_name)
            available_models[model_name] = new_model_instance

        if models_type := getattr(parent_module_instance, "MODELS_TYPE", None):
            setattr(parent_module_instance, models_type, list_of_available_model_names)
        return available_models

    @staticmethod
    def set_secret(required_secret):
        env_secret = None
        secret_str = f"{AppBase.app_config.app_name}_{required_secret}".upper()
        env_secret = os.environ.get(secret_str, None)
        if env_secret:
            AppBase.secrets[required_secret] = env_secret
        else:
            print(f"Secret: {required_secret} is None!")

    @staticmethod
    def get_requested_module_instance(available_module_instances, requested_module):
        for module_instance in available_module_instances:
            if module_instance.MODULE_NAME == requested_module or module_instance.MODULE_UI_NAME == requested_module:
                return module_instance

        return None

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
