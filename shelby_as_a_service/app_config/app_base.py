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
        if app_name is None:
            raise ValueError(
                "App must be initialized with an app_name before it can be used without it."
            )
        if app_name == "base":
            ConfigManager.check_and_create_base()
            app_name = ConfigManager.load_webui_sprite_default_config()

        app_config_file_dict = ConfigManager.load_app_config(app_name)
        AppBase.app_config = AppBase.AppConfigModel(**app_config_file_dict.get("app", {}))

        load_dotenv(os.path.join(f"app_config/your_apps/{app_name}", ".env"))

        AppBase.log = AppBase.get_logger(logger_name=app_name)

        AppBase.list_of_extension_configs = ConfigManager.get_extension_configs()

        AppBase.local_index_dir = f"app_config/your_apps/{app_name}/index"
        AppBase.the_context_index = ContextIndexService.TheContextIndex(
            **app_config_file_dict.get("index", {})
        )

        AppBase.load_sprite_instances(app_config_file_dict)

        ConfigManager.update_config_file_from_loaded_models()

        return cls

    @staticmethod
    def load_sprite_instances(app_config_file_dict: Dict[str, Any]):
        for sprite_name in AppBase.AVAILABLE_SPRITES:
            match sprite_name:
                case "webui_sprite":
                    from interfaces.webui.webui_sprite import WebUISprite

                    ConfigManager.add_extensions_to_sprite(
                        AppBase.list_of_extension_configs, WebUISprite
                    )
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
        if getattr(cls, "log", None) is None:
            if logger_name is None:
                raise ValueError(
                    "Logger must be initialized with an logger_name before it can be used without it."
                )
            cls.log = Logger(logger_name=logger_name)
        return cls.log

    @classmethod
    def run_sprites(cls):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in AppBase.app_config.enabled_sprites:
                sprite = getattr(cls, sprite_name)
                executor.submit(sprite.run_sprite())
