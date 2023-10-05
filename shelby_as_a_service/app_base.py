import concurrent.futures
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, TypeVar

from dotenv import load_dotenv
from modules.utils.app_manager import AppManager
from modules.utils.log_service import Logger
from pydantic import BaseModel

T_Config = TypeVar("T_Config", bound=BaseModel)


class AppInstance:
    AVAILABLE_SPRITES: List[str] = ["web_sprite", "discord_sprite", "slack_sprite"]

    app_name: str = "base"
    enabled_sprites: List[str] = ["web_sprite"]
    secrets: Dict[str, str] = {}
    total_cost: Decimal = Decimal("0")
    last_request_cost: Decimal = Decimal("0")

    def setup_app(self, app_name):
        self.app_name = app_name
        self.log = AppBase.get_logger(logger_name=app_name)
        # self.app_name = AppManager.initialize_app_config(app_name)

        load_dotenv(os.path.join(f"apps/{self.app_name}/", ".env"))
        AppBase.app_config_dict = AppManager.load_app_file(self.app_name)

        # Index needs to init first
        from modules.index.index_service import IndexService

        self.local_index_dir = f"apps/{self.app_name}/index"
        self.index_service = IndexService()
        self.index = self.index_service.index_instance

        for sprite_name in self.AVAILABLE_SPRITES:
            if sprite_name in self.enabled_sprites:
                match sprite_name:
                    case "web_sprite":
                        from sprites.web.web_sprite import WebSprite

                        self.web_sprite = WebSprite()
                    case "discord_sprite":
                        from sprites.discord_sprite import DiscordSprite

                        self.discord_sprite = DiscordSprite()
                    case "slack_sprite":
                        from sprites.slack_sprite import SlackSprite

                        self.discord_sprite = SlackSprite()
                    case _:
                        print("oops")

    def run_sprites(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in self.enabled_sprites:
                sprite = getattr(self, sprite_name)
                executor.submit(sprite.run_sprite())


class AppBase:
    APP_CONFIG_TYPE: str = "app_instance"
    PROMPT_TEMPLATE_DIR: str = "shelby_as_a_service/modules/prompt_templates"

    _instance: AppInstance
    _log: Logger

    app_name: str
    index: Type
    app_config_dict: Dict[str, Any]

    @classmethod
    def get_app(cls, app_name: Optional[str] = None) -> AppInstance:
        if getattr(cls, "_instance", None) is None:
            if app_name is None:
                raise ValueError(
                    "AppInstance must be initialized with an app_name before it can be used without it."
                )
            cls._instance = AppInstance()
            cls.app_name = cls._instance.app_name
        return cls._instance

    @classmethod
    def get_logger(cls, logger_name: Optional[str] = None) -> Logger:
        if getattr(cls, "_log", None) is None:
            if logger_name is None:
                raise ValueError(
                    "Logger must be initialized with an logger_name before it can be used without it."
                )
            cls._log = Logger(logger_name=logger_name)
        return cls._log

    @staticmethod
    def load_service_config(
        class_instance: Type,
        config_class: Type[T_Config],
    ) -> T_Config:
        AppBase.set_secrets(class_instance)

        class_config_dict = AppBase.get_config_dict(
            class_config_path=class_instance.class_config_path
        )
        if class_config_dict is None:
            AppBase.add_class_config_to_config_file(
                config_class=config_class,
                class_config_path=class_instance.class_config_path,
            )

        return AppBase.create_config_instance(
            config_class=config_class,
            class_config_dict=class_config_dict,
        )

    @staticmethod
    def set_secrets(class_instance: Type):
        if (
            hasattr(class_instance, "REQUIRED_SECRETS")
            and class_instance.REQUIRED_SECRETS
        ):
            for secret in class_instance.REQUIRED_SECRETS:
                env_secret = None
                secret_str = f"{AppBase.app_name}_{secret}".upper()
                env_secret = os.environ.get(secret_str, None)
                if env_secret:
                    AppBase._instance.secrets[secret] = env_secret
                else:
                    print(f"Secret: {secret} is None!")

    @staticmethod
    def get_config_path(
        parent_config_path: List[str], class_config_type: str, class_name: str
    ) -> List[str]:
        config_path = parent_config_path.copy()
        config_path.extend([class_config_type, class_name])
        return config_path

    @staticmethod
    def get_config_dict(
        class_config_path: Optional[List[str]],
    ) -> Optional[Dict[str, Any]]:
        if class_config_path is None:
            return None
        config = None
        # Create a copy of the base config, and path to the config
        config = AppBase.app_config_dict.copy()
        for path in class_config_path:
            config = config.get(path, None)
            if config is None:
                config = None
                break

        return config

    @staticmethod
    def create_config_instance(
        config_class: Type[T_Config],
        class_config_dict: Optional[Dict[str, Any]],
    ) -> T_Config:
        if class_config_dict:
            config_class_instance = config_class(**class_config_dict, extra="ignore")
        else:
            config_class_instance = config_class()

        return config_class_instance

    @staticmethod
    def add_class_config_to_config_file(
        config_class: Type[T_Config], class_config_path: List[str]
    ):
        def update(config_dict, config_path, config_class):
            if len(config_path) == 1:
                config_instance = config_class()
                config_dict[config_path[0]] = config_instance.model_dump()
            else:
                path = config_path.pop(0)
                config_dict[path] = update(
                    config_dict.get(path, {}), config_path, config_class
                )
            return config_dict

        updated_app_config_dict = AppBase.app_config_dict.copy()
        updated_app_config_dict = update(
            updated_app_config_dict, class_config_path, config_class
        )

        AppManager.save_app_file(
            AppBase.app_name, updated_app_config_dict=updated_app_config_dict
        )
        AppBase.app_config_dict = updated_app_config_dict
