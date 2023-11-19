import concurrent.futures
import logging
import os
from decimal import Decimal
from typing import Any, Optional, Type

from app.config_manager import ConfigManager
from dotenv import load_dotenv
from pydantic import BaseModel


class AppBase:
    """
    The base of the Shelby as a Service application.
    Responsible for loading the app and it's required services from a config file.

    Methods:
    - setup_app(cls, app_name): Sets up the application with the given app_name.
    - _get_logger(cls, logger_name: Optional[str] = None) -> Logger: Returns a logger instance.
    - run_sprites(cls): Runs the enabled sprites.
    """

    APP_DIR_PATH: str = "app/your_apps"

    class ClassConfigModel(BaseModel):
        """
        A class representing the application configuration model.

        Attributes:
        - app_name: A string representing the application name.
        - enabled_sprites: A list of enabled sprites.
        - enabled_extensions: A list of enabled extensions.
        - disabled_extensions: A list of disabled extensions.
        """

        app_name: str = "base"
        enabled_sprites: list[str] = ["webui_sprite"]
        enabled_extensions: list[str] = []
        disabled_extensions: list[str] = []

    app_config: ClassConfigModel

    log: "LoggerWrapper"

    enabled_sprite_instances: list[Type] = []
    list_of_extension_configs: list[Any]

    secrets: dict[str, str] = {}

    total_cost: Decimal = Decimal("0")
    last_request_cost: Decimal = Decimal("0")

    @classmethod
    def setup_app(cls, app_name):
        """
        Sets up the application with the given app_name.

        Args:
        - app_name: A string representing the application name.

        Returns:
        - cls: The AppBase class.
        """
        if app_name is None:
            raise ValueError(
                "App must be initialized with an app_name before it can be used without it."
            )
        if app_name == "base":
            ConfigManager.check_and_create_base()
            app_name = ConfigManager.load_webui_sprite_default_config()

        config_file_dict = ConfigManager.load_app(app_name)
        AppBase.app_config = AppBase.ClassConfigModel(**config_file_dict.get("app", {}))
        AppBase._get_logger(logger_name=app_name)
        AppBase.log.info(f"Setting up shelby_as_a_service app instance with name: {app_name}...")

        load_dotenv(os.path.join(AppBase.APP_DIR_PATH, app_name, ".env"))

        AppBase.list_of_extension_configs = ConfigManager.get_extension_configs()
        cls.local_index_dir = os.path.join(cls.APP_DIR_PATH, cls.app_config.app_name, "index")
        from context_index.doc_index.doc_index import DocIndex

        AppBase.doc_index: DocIndex = DocIndex()

        AppBase._load_sprite_instances(config_file_dict)

        ConfigManager.update_config_file_from_loaded_models()

        return cls

    @staticmethod
    def _load_sprite_instances(config_file_dict: dict[str, Any]):
        """
        Loads the sprite instances.

        Args:
        - config_file_dict: A dictionary representing the application configuration file.

        Returns:
        - None
        """
        import interfaces as interfaces

        AppBase.AVAILABLE_SPRITES: list[Type] = interfaces.AVAILABLE_SPRITES
        AppBase.AVAILABLE_SPRITES_TYPINGS = interfaces.AVAILABLE_SPRITES_TYPINGS
        AppBase.AVAILABLE_SPRITES_UI_NAMES: list[str] = interfaces.AVAILABLE_SPRITES_UI_NAMES
        for sprite in AppBase.AVAILABLE_SPRITES:
            if sprite.CLASS_NAME in AppBase.app_config.enabled_sprites:
                # ConfigManager.add_extensions_to_sprite(
                #     AppBase.list_of_extension_configs, sprite
                # )

                AppBase.enabled_sprite_instances.append(sprite(config_file_dict=config_file_dict))

            # case "discord_sprite":
            #     from interfaces.bots.discord_sprite import DiscordSprite

            # ConfigManager.add_extensions_to_sprite(AppBase.list_of_extension_configs, DiscordSprite)
            #     AppBase.discord_sprite = sprite(config_file_dict)

            #     AppBase.enabled_sprite_instances.append(AppBase.discord_sprite)

            # case "slack_sprite":
            #     from interfaces.bots.slack_sprite import SlackSprite

            # ConfigManager.add_extensions_to_sprite(AppBase.list_of_extension_configs, SlackSprite)
            #     AppBase.slack_sprite = sprite(config_file_dict)

            #     AppBase.enabled_sprite_instances.append(AppBase.slack_sprite)

    @classmethod
    def _get_logger(cls, logger_name: Optional[str] = None):
        """
        Returns a logger instance.

        Args:
        - logger_name: A string representing the logger name.

        Returns:
        - Logger: A logger instance.
        """
        if getattr(cls, "logger", None) is None:
            if logger_name is None:
                raise ValueError(
                    "Logger must be initialized with an logger_name before it can be used without it."
                )

            logs_dir = os.path.join(AppBase.APP_DIR_PATH, AppBase.app_config.app_name, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            log_file_path = os.path.join(logs_dir, f"{logger_name}.log")

            logging.basicConfig(
                filename=log_file_path,
                filemode="a",
                encoding="utf-8",
                level=logging.ERROR,
                format="%(levelname)s: %(asctime)s %(message)s",
                datefmt="%Y/%m/%d %I:%M:%S %p",
            )

            AppBase.log = LoggerWrapper(logger_name)

    @classmethod
    def run_sprites(cls):
        """
        Runs the sprites.
        """

        def run_sprite_with_restart(sprite):
            while True:
                try:
                    sprite.run_sprite()
                except Exception as e:
                    AppBase.log.error(f"Sprite crashed with error: {e}. Restarting...")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite in AppBase.enabled_sprite_instances:
                sprite.run_sprite()
                # executor.submit(run_sprite_with_restart, sprite)

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


class LoggerWrapper:
    def __init__(self, class_name: str):
        self.log = logging.getLogger()
        self.log.setLevel(logging.INFO)
        self.class_name = class_name

    def addHandler(self, handler):
        self.log.addHandler(handler)

    def removeHandler(self, handler):
        self.log.removeHandler(handler)

    def info(self, msg, *args, **kwargs):
        self.log.info(f"In {self.class_name}: {msg}", *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.log.debug(f"In {self.class_name}: {msg}", *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log.warning(f"In {self.class_name}: {msg}", *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log.error(f"In {self.class_name}: {msg}", *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.log.critical(f"In {self.class_name}: {msg}", *args, **kwargs)
