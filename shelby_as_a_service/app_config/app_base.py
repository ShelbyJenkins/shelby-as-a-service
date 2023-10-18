import concurrent.futures
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from app_config.config_manager import ConfigManager
from app_config.context_index.index_base import ContextIndexService
from app_config.log_service import Logger
from dotenv import load_dotenv
from pydantic import BaseModel


class AppBase:
    """
    The base of the Shelby as a Service application.
    Responsible for loading the app and it's required services from a config file.

    Methods:
    - setup_app(cls, app_name): Sets up the application with the given app_name.
    - get_logger(cls, logger_name: Optional[str] = None) -> Logger: Returns a logger instance.
    - run_sprites(cls): Runs the enabled sprites.
    """

    AVAILABLE_SPRITES: List[str] = ["webui_sprite"]
    # AVAILABLE_SPRITES: List[str] = ["webui_sprite", "discord_sprite", "slack_sprite"]
    webui_sprite: Type
    discord_sprite: Type
    slack_sprite: Type
    available_sprite_instances: List[Any] = []
    log: Logger
    context_index_service = ContextIndexService
    the_context_index: ContextIndexService.TheContextIndex

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
        enabled_sprites: List[str] = ["webui_sprite"]
        enabled_extensions: List[str] = []
        disabled_extensions: List[str] = []

    app_config: AppConfigModel
    list_of_extension_configs: List[Any]
    secrets: Dict[str, str] = {}
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
            raise ValueError("App must be initialized with an app_name before it can be used without it.")
        if app_name == "base":
            ConfigManager.check_and_create_base()
            app_name = ConfigManager.load_webui_sprite_default_config()

        app_config_file_dict = ConfigManager.load_app_config(app_name)
        AppBase.app_config = AppBase.AppConfigModel(**app_config_file_dict.get("app", {}))

        load_dotenv(os.path.join(f"app_config/your_apps/{app_name}", ".env"))

        AppBase.log = AppBase.get_logger(logger_name=app_name)

        AppBase.list_of_extension_configs = ConfigManager.get_extension_configs()

        AppBase.local_index_dir = f"app_config/your_apps/{app_name}/index"
        AppBase.the_context_index = ContextIndexService.TheContextIndex(**app_config_file_dict.get("index", {}))

        AppBase._load_sprite_instances(app_config_file_dict)

        ConfigManager.update_config_file_from_loaded_models()

        return cls

    @staticmethod
    def _load_sprite_instances(app_config_file_dict: Dict[str, Any]):
        """
        Loads the sprite instances.

        Args:
        - app_config_file_dict: A dictionary representing the application configuration file.

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
                    AppBase.webui_sprite = WebUISprite(app_config_file_dict)

                    AppBase.available_sprite_instances.append(AppBase.webui_sprite)

                # case "discord_sprite":
                #     from interfaces.bots.discord_sprite import DiscordSprite

                # ConfigManager.add_extensions_to_sprite(AppBase.list_of_extension_configs, DiscordSprite)
                #     AppBase.discord_sprite = DiscordSprite(app_config_file_dict)

                #     AppBase.available_sprite_instances.append(AppBase.discord_sprite)

                # case "slack_sprite":
                #     from interfaces.bots.slack_sprite import SlackSprite

                # ConfigManager.add_extensions_to_sprite(AppBase.list_of_extension_configs, SlackSprite)
                #     AppBase.slack_sprite = SlackSprite(app_config_file_dict)

                #     AppBase.available_sprite_instances.append(AppBase.slack_sprite)

                case _:
                    print("oops")

    @classmethod
    def get_logger(cls, logger_name: Optional[str] = None) -> Logger:
        """
        Returns a logger instance.

        Args:
        - logger_name: A string representing the logger name.

        Returns:
        - Logger: A logger instance.
        """
        if getattr(cls, "log", None) is None:
            if logger_name is None:
                raise ValueError("Logger must be initialized with an logger_name before it can be used without it.")
            cls.log = Logger(logger_name=logger_name)
        return cls.log

    @classmethod
    def run_sprites(cls):
        """
        Runs the sprites.

        Args:
        - None

        Returns:
        - None
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in AppBase.app_config.enabled_sprites:
                sprite = getattr(cls, sprite_name)
                executor.submit(sprite.run_sprite())
