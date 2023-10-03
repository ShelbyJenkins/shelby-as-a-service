import concurrent.futures
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, Union

from dotenv import load_dotenv
from modules.utils.app_manager import AppManager
from modules.utils.config_manager import ConfigManager
from modules.utils.log_service import Logger
from pydantic import Field


class AppInstance:
    app_name: str

    config: Dict[str, str] = {}
    secrets: Dict[str, str] = {}
    required_secrets: List[str] = []
    total_cost: Decimal = Decimal("0")
    last_request_cost: Decimal = Decimal("0")

    def __init__(self, app_name):
        self.app_name = app_name
        self.log = Logger(app_name=app_name)

    def setup_app(self) -> "AppInstance":
        # self.app_name = AppManager.initialize_app_config(app_name)

        load_dotenv(os.path.join(f"apps/{self.app_name}/", ".env"))
        self.config = AppManager.load_app_file(self.app_name)
        self.local_index_dir = f"apps/{self.app_name}/index"
        from modules.index.index_model import IndexModel

        # Index needs to init first
        self.index = IndexModel()

        from sprites.discord_sprite import DiscordSprite
        from sprites.web.web_sprite import WebSprite

        # self.web_sprite = WebSprite()
        self.discord_sprite = DiscordSprite()

        # Check secrets
        for secret in self.required_secrets:
            if self.secrets.get(secret, None) is None:
                print(f"Secret: {secret} is None!")

        return self

    def run_sprites(self):
        self.discord_sprite.run_sprite()
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        # for sprite_name in self.enabled_sprites:
        #     sprite = getattr(self, sprite_name)
        #     executor.submit(sprite.run_sprite())


class AppBase:
    _instance: AppInstance

    app_manager: Type[AppManager] = AppManager
    config_manager: Type[ConfigManager] = ConfigManager

    prompt_template_dir: str = "shelby_as_a_service/modules/prompt_templates"

    app_config_path: str = "app_instance"
    index_config_path: List[str] = ["app_instance", "index"]
    sprite_config_path: str = "services"
    agent_config_path: str = "services"
    service_config_path: str = "services"
    provider_config_path: str = "services"

    @classmethod
    def get_app(cls, app_name: Optional[str] = None) -> AppInstance:
        if getattr(cls, "_instance", None) is None:
            if app_name is None:
                raise ValueError(
                    "AppInstance must be initialized with an app_name before it can be used without it."
                )
            cls._instance = AppInstance(app_name=app_name)
        return cls._instance

    @staticmethod
    def setup_service_config(instance):
        instance.log = instance.app.log
        instance.index = instance.app.index
        instance.app_name = instance.app.app_name
        config_path = AppBase.get_config_path(instance)
        config = AppBase.get_config(instance, config_path)
        AppBase.set_config(instance, config)

    @staticmethod
    def get_config_path(instance) -> Optional[List[str]]:
        """Builds path to the service settings in the config file"""

        base_path = [AppBase.app_config_path]

        base_path.append(AppBase.sprite_config_path)
        if sprite_name := getattr(instance, "sprite_name", None):
            base_path.append(sprite_name)
            return base_path

        base_path.extend(
            [instance.parent_sprite.sprite_name, AppBase.agent_config_path]
        )
        if agent_name := getattr(instance, "agent_name", None):
            base_path.append(agent_name)
            return base_path

        base_path.extend(
            [instance.parent_agent.agent_name, AppBase.service_config_path]
        )
        if service_name := getattr(instance, "service_name", None):
            base_path.append(service_name)
            return base_path

        base_path.extend(
            [instance.parent_service.service_name, AppBase.provider_config_path]
        )
        if provider_name := getattr(instance, "provider_name", None):
            base_path.append(provider_name)
            return base_path

        return None

    @staticmethod
    def get_config(
        instance, config_path=None, input_config=None
    ) -> Optional[Dict[str, Any]]:
        config = None
        if config_path is None and input_config is None:
            if instance.__class__.__name__ == "IndexModel":
                config_path = AppBase.index_config_path
            else:
                return None
        if config_path and input_config is None:
            # Create a copy of the base config, and path to the config
            config = instance.app.config.copy()
            for path in config_path:
                config = config.get(path, None)
                if config is None:
                    config = None
                    break
        elif input_config and config_path is None:
            config = input_config

        return config

    @staticmethod
    def set_config(instance, config):
        # from_file overwrites class vars from file
        config = {**vars(instance), **(config or {})}

        # Removes services object used to structure the json file
        if config.get("services", None):
            config.pop("services")

        for key, value in config.copy().items():
            if ConfigManager.check_for_ignored_objects(
                key
            ) and ConfigManager.check_for_ignored_objects(value):
                setattr(instance, key, value)
            else:
                config.pop(key)

        instance.config = config

        if hasattr(instance, "required_secrets") and instance.required_secrets:
            for secret in instance.required_secrets:
                secret_str = f"{instance.app.app_name}_{secret}".upper()
                env_secret = os.environ.get(secret_str)

                instance.app.secrets[secret] = env_secret
                instance.app.required_secrets.append(secret)
