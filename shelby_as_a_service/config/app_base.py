import concurrent.futures
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from config.app_manager import AppManager
from dotenv import load_dotenv
from modules.utils.log_service import Logger
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

        app_config_file_dict = AppManager.load_app_file(app_name)
        AppBase.config = AppBase.AppConfigModel(**app_config_file_dict)

        list_of_sprite_classes = AppBase.get_sprites(AppBase.AVAILABLE_SPRITES)
        sprites_config = app_config_file_dict.get("sprites", {})

        for sprite in list_of_sprite_classes:
            sprite_config = sprites_config.get(sprite.SPRITE_NAME, {})
            sprite_instance = sprite(sprite_config=sprite_config)
            setattr(
                AppBase,
                sprite.SPRITE_NAME,
                sprite_instance,
            )
            AppBase.available_sprite_instances.append(sprite_instance)

        AppBase.index = IndexBase.IndexConfigModel(**app_config_file_dict.get("index", {}))

        AppBase.update_config_file_from_loaded_models()

    @staticmethod
    def get_sprites(list_of_sprite_names: List[str]):
        list_of_sprite_classes = []
        for sprite_name in list_of_sprite_names:
            match sprite_name:
                case "webui_sprite":
                    from sprites.webui.webui_sprite import WebUISprite

                    list_of_sprite_classes.append(WebUISprite)
                case "discord_sprite":
                    from sprites.discord_sprite import DiscordSprite

                    list_of_sprite_classes.append(DiscordSprite)
                case "slack_sprite":
                    from sprites.slack_sprite import SlackSprite

                    list_of_sprite_classes.append(SlackSprite)
                case _:
                    print("oops")

        return list_of_sprite_classes

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
        old_app_config_file_dict = AppManager.load_app_file(AppBase.config.app_name)

        new_config_dict = {}
        new_config_dict["app"] = {
            **AppBase.config.model_dump(),
            **old_app_config_file_dict.get("app", {}),
        }
        new_config_dict["index"] = {
            **AppBase.index.model_dump(),
            **old_app_config_file_dict.get("index", {}),
        }

        new_config_dict["sprites"] = {}
        new_sprites_config = new_config_dict["sprites"]
        old_sprites_config = old_app_config_file_dict.get("sprites", {})

        for sprite in AppBase.available_sprite_instances:
            sprite_instance_config = old_sprites_config.get(sprite.SPRITE_NAME, {})
            new_sprites_config[sprite.SPRITE_NAME] = {
                **sprite.config.model_dump(),
                **sprite_instance_config,
            }

            for agent in sprite.available_agent_instances:
                new_sprites_config[sprite.SPRITE_NAME]["agents"] = {}
                new_agents_config = new_sprites_config[sprite.SPRITE_NAME]["agents"]
                old_agents_config = old_sprites_config.get("agents", {})
                agent_instance_config = old_agents_config.get(agent.AGENT_NAME, {})
                new_agents_config[agent.AGENT_NAME] = {
                    **agent.config.model_dump(),
                    **agent_instance_config,
                }

                for service in agent.available_service_instances:
                    new_agents_config[agent.AGENT_NAME]["services"] = {}
                    new_services_config = new_agents_config[agent.AGENT_NAME]["services"]
                    old_services_config = old_agents_config.get("services", {})
                    service_instance_config = old_services_config.get(service.SERVICE_NAME, {})
                    new_services_config[service.SERVICE_NAME] = {
                        **service.config.model_dump(),
                        **service_instance_config,
                    }

                    for provider in service.available_provider_instances:
                        new_services_config[service.SERVICE_NAME]["providers"] = {}
                        new_providers_config = new_services_config[service.SERVICE_NAME][
                            "providers"
                        ]
                        old_providers_config = old_services_config.get("providers", {})
                        provider_instance_config = old_providers_config.get(
                            provider.PROVIDER_NAME, {}
                        )
                        new_providers_config[provider.PROVIDER_NAME] = {
                            **provider.config.model_dump(),
                            **provider_instance_config,
                        }

        AppManager.save_app_file(AppBase.config.app_name, new_config_dict)
