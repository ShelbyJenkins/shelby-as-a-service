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

    AVAILABLE_SPRITES: list[str] = ["webui_sprite"]
    # AVAILABLE_SPRITES: list[str] = ["webui_sprite", "discord_sprite", "slack_sprite"]
    APP_DIR_PATH: str = "app/your_apps"

    class AppConfigModel(BaseModel):
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

    app_config: AppConfigModel

    webui_sprite: Type
    discord_sprite: Type
    slack_sprite: Type

    log: logging.Logger

    available_sprite_instances: list[Any] = []
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

        app_file_dict = ConfigManager.load_app(app_name)
        AppBase.app_config = AppBase.AppConfigModel(**app_file_dict.get("app", {}))
        AppBase._get_logger(logger_name=app_name)
        AppBase.log.info(f"Setting up app instance: {app_name}...")

        load_dotenv(os.path.join(AppBase.APP_DIR_PATH, app_name, ".env"))

        AppBase.list_of_extension_configs = ConfigManager.get_extension_configs()
        cls.local_index_dir = os.path.join(cls.APP_DIR_PATH, cls.app_config.app_name, "index")
        from services.context_index.context_index import ContextIndex

        AppBase.context_index: ContextIndex = ContextIndex()

        AppBase._load_sprite_instances(app_file_dict)

        ConfigManager.update_config_file_from_loaded_models()

        return cls

    @staticmethod
    def _load_sprite_instances(app_file_dict: dict[str, Any]):
        """
        Loads the sprite instances.

        Args:
        - app_file_dict: A dictionary representing the application configuration file.

        Returns:
        - None
        """
        for sprite_name in AppBase.AVAILABLE_SPRITES:
            match sprite_name:
                case "webui_sprite":
                    from interfaces.webui.webui_sprite import WebUISprite

                    # ConfigManager.add_extensions_to_sprite(
                    #     AppBase.list_of_extension_configs, WebUISprite
                    # )
                    AppBase.webui_sprite = WebUISprite(app_file_dict)

                    AppBase.available_sprite_instances.append(AppBase.webui_sprite)

                # case "discord_sprite":
                #     from interfaces.bots.discord_sprite import DiscordSprite

                # ConfigManager.add_extensions_to_sprite(AppBase.list_of_extension_configs, DiscordSprite)
                #     AppBase.discord_sprite = DiscordSprite(app_file_dict)

                #     AppBase.available_sprite_instances.append(AppBase.discord_sprite)

                # case "slack_sprite":
                #     from interfaces.bots.slack_sprite import SlackSprite

                # ConfigManager.add_extensions_to_sprite(AppBase.list_of_extension_configs, SlackSprite)
                #     AppBase.slack_sprite = SlackSprite(app_file_dict)

                #     AppBase.available_sprite_instances.append(AppBase.slack_sprite)

                case _:
                    print("oops")

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
                level=logging.DEBUG,
                format="%(levelname)s: %(asctime)s %(message)s",
                datefmt="%Y/%m/%d %I:%M:%S %p",
            )
            AppBase.log = logging.getLogger(__name__)

    @classmethod
    def run_sprites(cls):
        """
        Runs the sprites.

        Args:
        - None

        Returns:
        - None
        """

        def run_sprite_with_restart(sprite):
            while True:
                try:
                    sprite.run_sprite()
                except Exception as e:
                    AppBase.log.error(f"Sprite crashed with error: {e}. Restarting...")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in AppBase.app_config.enabled_sprites:
                sprite = getattr(cls, sprite_name)
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
