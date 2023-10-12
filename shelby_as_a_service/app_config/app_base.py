import concurrent.futures
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from app_config.app_manager import AppManager
from app_config.log_service import Logger
from dotenv import load_dotenv
from pydantic import BaseModel
from services.index.index_base import IndexBase


class AppBase:
    AVAILABLE_SPRITES: List[str] = ["webui_sprite"]
    # AVAILABLE_SPRITES: List[str] = ["webui_sprite", "discord_sprite", "slack_sprite"]
    PROMPT_TEMPLATE_DIR: str = "shelby_as_a_service/modules/prompt_templates"
    CLASS_CONFIG_TYPE: str = "app"

    class AppConfigModel(BaseModel):
        app_name: str = "base"
        enabled_sprites: List[str] = ["webui_sprite"]

    config: AppConfigModel
    available_sprite_instances: List[Any] = []
    webui_sprite: Type
    discord_sprite: Type
    slack_sprite: Type
    app_config_file_dict: Dict[str, Any]
    app_name: str
    secrets: Dict[str, str] = {}
    log: Logger
    index: IndexBase.IndexConfigModel
    total_cost: Decimal = Decimal("0")
    last_request_cost: Decimal = Decimal("0")

    @classmethod
    def create_app(cls, app_name: Optional[str] = None):
        if app_name is None:
            raise ValueError(
                "App must be initialized with an app_name before it can be used without it."
            )
        AppBase.setup_app(app_name=app_name)
        return cls

    @classmethod
    def setup_app(cls, app_name):
        AppBase.app_name = app_name

        if AppBase.app_name == "base":
            AppManager.check_and_create_base()
            # AppBase.update_app_config_file_from_default("base")
            # AppBase.app_name = AppManager.load_webui_sprite_default_app()
            # if AppBase.app_name != "base":
            #     AppBase.update_app_config_file_from_default(AppBase.app_name)

        AppBase.local_index_dir = f"apps/{AppBase.app_name}/index"
        AppBase.app_dir = f"apps/{AppBase.app_name}/"
        load_dotenv(os.path.join(AppBase.app_dir, ".env"))
        AppBase.log = AppBase.get_logger(logger_name=AppBase.app_name)

        AppBase.app_config_file_dict = AppManager.load_app_file(app_name)
        AppBase.config = AppBase.AppConfigModel(**AppBase.app_config_file_dict.get("app", {}))

        AppBase.get_sprites()

        AppBase.index = IndexBase.IndexConfigModel(**AppBase.app_config_file_dict.get("index", {}))

        AppBase.update_config_file_from_loaded_models()

    @staticmethod
    def get_sprites():
        for sprite_name in AppBase.AVAILABLE_SPRITES:
            match sprite_name:
                case "webui_sprite":
                    from interfaces.webui.webui_sprite import WebUISprite

                    AppBase.webui_sprite = WebUISprite(AppBase.app_config_file_dict)

                    AppBase.available_sprite_instances.append(AppBase.webui_sprite)

                # case "discord_sprite":
                #     from interfaces.bots.discord_sprite import DiscordSprite

                #     AppBase.discord_sprite = DiscordSprite(AppBase.app_config_file_dict)

                #     AppBase.available_sprite_instances.append(AppBase.discord_sprite)

                # case "slack_sprite":
                #     from interfaces.bots.slack_sprite import SlackSprite

                #     AppBase.slack_sprite = SlackSprite(AppBase.app_config_file_dict)

                #     AppBase.available_sprite_instances.append(AppBase.slack_sprite)

                case _:
                    print("oops")

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
                secret_str = f"{AppBase.app_name}_{secret}".upper()
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
