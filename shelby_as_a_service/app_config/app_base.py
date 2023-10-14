import concurrent.futures
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from app_config.app_manager import AppManager
from app_config.context_index.index_base import IndexBase
from app_config.log_service import Logger
from dotenv import load_dotenv
from pydantic import BaseModel


class AppBase:
    AVAILABLE_SPRITES: List[str] = ["webui_sprite"]
    # AVAILABLE_SPRITES: List[str] = ["webui_sprite", "discord_sprite", "slack_sprite"]
    webui_sprite: Type
    discord_sprite: Type
    slack_sprite: Type
    available_sprite_instances: List[Any] = []
    log: Logger
    index: IndexBase.IndexConfigModel

    class AppConfigModel(BaseModel):
        app_name: str = "base"
        enabled_sprites: List[str] = ["webui_sprite"]
        enabled_extensions: List[str] = []

    config: AppConfigModel
    list_of_extension_configs: Dict[str, Any]
    secrets: Dict[str, str] = {}
    total_cost: Decimal = Decimal("0")
    last_request_cost: Decimal = Decimal("0")

    @classmethod
    def setup_app(cls, app_name):
        if app_name is None:
            raise ValueError(
                "App must be initialized with an app_name before it can be used without it."
            )

        if app_name == "base":
            AppManager.check_and_create_base()
            app_name = AppManager.load_webui_sprite_default_app()

        app_config_file_dict = AppManager.load_app_file(app_name)
        AppBase.config = AppBase.AppConfigModel(**app_config_file_dict.get("app", {}))

        load_dotenv(os.path.join(f"app_config/your_apps/{app_name}", ".env"))

        AppBase.log = AppBase.get_logger(logger_name=app_name)
        AppBase.list_of_extension_configs = AppManager.get_extension_configs()

        AppBase.load_sprite_instances(app_config_file_dict)

        AppBase.local_index_dir = f"app_config/your_apps/{app_name}/index"
        AppBase.index = IndexBase.IndexConfigModel(**app_config_file_dict.get("index", {}))

        AppBase.update_config_file_from_loaded_models()

        return cls

    @staticmethod
    def load_sprite_instances(app_config_file_dict: Dict[str, Any]):
        for sprite_name in AppBase.AVAILABLE_SPRITES:
            match sprite_name:
                case "webui_sprite":
                    from interfaces.webui.webui_sprite import WebUISprite

                    AppManager.add_extensions_to_sprite(
                        AppBase.list_of_extension_configs, WebUISprite
                    )
                    AppBase.webui_sprite = WebUISprite(app_config_file_dict)

                    AppBase.available_sprite_instances.append(AppBase.webui_sprite)

                # case "discord_sprite":
                #     from interfaces.bots.discord_sprite import DiscordSprite

                # AppManager.add_extensions_to_sprite(AppBase.list_of_extension_configs, DiscordSprite)
                #     AppBase.discord_sprite = DiscordSprite(app_config_file_dict)

                #     AppBase.available_sprite_instances.append(AppBase.discord_sprite)

                # case "slack_sprite":
                #     from interfaces.bots.slack_sprite import SlackSprite

                # AppManager.add_extensions_to_sprite(AppBase.list_of_extension_configs, SlackSprite)
                #     AppBase.slack_sprite = SlackSprite(app_config_file_dict)

                #     AppBase.available_sprite_instances.append(AppBase.slack_sprite)

                case _:
                    print("oops")

    @staticmethod
    def create_extension_module_instances(parent_instance, module_config_file_dict=None):
        for module in parent_instance.extension_modules:
            if module_name := getattr(module, "MODULE_NAME", None):
                module_instance = module(module_config_file_dict)
                setattr(parent_instance, module_name, module_instance)

    @classmethod
    def get_logger(cls, logger_name: Optional[str] = None) -> Logger:
        if getattr(cls, "log", None) is None:
            if logger_name is None:
                raise ValueError(
                    "Logger must be initialized with an logger_name before it can be used without it."
                )
            cls.log = Logger(logger_name=logger_name)
        return cls.log

    @staticmethod
    def set_secrets(class_instance: Type):
        if hasattr(class_instance, "REQUIRED_SECRETS") and class_instance.REQUIRED_SECRETS:
            for secret in class_instance.REQUIRED_SECRETS:
                env_secret = None
                secret_str = f"{AppBase.config.app_name}_{secret}".upper()
                env_secret = os.environ.get(secret_str, None)
                if env_secret:
                    AppBase.secrets[secret] = env_secret
                else:
                    print(f"Secret: {secret} is None!")

    @classmethod
    def run_sprites(cls):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in cls.config.enabled_sprites:
                sprite = getattr(cls, sprite_name)
                executor.submit(sprite.run_sprite())

    @classmethod
    def update_config_file_from_loaded_models(cls):
        # old_config_dict = AppManager.load_app_file(AppBase.config.app_name)
        def recurse(module_instance, config_dict):
            config_dict[module_instance.MODULE_NAME] = module_instance.config.model_dump()
            module_config_dict = config_dict[module_instance.MODULE_NAME]
            if required_modules := getattr(module_instance, "REQUIRED_MODULES", None):
                for child_module in required_modules:
                    child_module_instance = getattr(module_instance, child_module.MODULE_NAME)
                    recurse(child_module_instance, module_config_dict)

        app_config_dict = {}
        app_config_dict["app"] = AppBase.config.model_dump()

        app_config_dict["index"] = AppBase.index.model_dump()

        for sprite in AppBase.available_sprite_instances:
            recurse(sprite, app_config_dict)

        AppManager.save_app_file(AppBase.config.app_name, app_config_dict)

    @staticmethod
    def get_list_of_module_instances(parent_class, available_modules):
        list_of_module_instances = []
        for module in available_modules:
            list_of_module_instances.append(getattr(parent_class, module.MODULE_NAME, None))
        return list_of_module_instances

    @staticmethod
    def get_requested_module_instance(available_module_instances, requested_module):
        for module_instance in available_module_instances:
            if module_instance.MODULE_NAME == requested_module:
                return module_instance
            else:
                return None

    @staticmethod
    def get_model(provider_instance, requested_model_name=None):
        model_instance = None
        available_models = getattr(provider_instance, "AVAILABLE_MODELS", [])
        if requested_model_name:
            for model in available_models:
                if model.MODEL_NAME == requested_model_name:
                    model_instance = model
                    break
        if model_instance is None:
            for model in available_models:
                if model.MODEL_NAME == provider_instance.config.model:
                    model_instance = model
                    break
        if model_instance is None:
            raise ValueError("model_instance must not be None in AppBase")
        return model_instance
