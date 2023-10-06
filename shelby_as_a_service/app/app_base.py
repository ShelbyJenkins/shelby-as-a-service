import concurrent.futures
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from app.app_manager import AppManager
from app.index.index_base import IndexBase
from dotenv import load_dotenv
from modules.utils.log_service import Logger
from pydantic import BaseModel

ConfigModelType = TypeVar("ConfigModelType", bound=BaseModel)


class AppBase:
    AVAILABLE_SPRITES: List[str] = ["web_sprite"]
    # AVAILABLE_SPRITES: List[str] = ["web_sprite", "discord_sprite", "slack_sprite"]
    PROMPT_TEMPLATE_DIR: str = "shelby_as_a_service/modules/prompt_templates"
    CLASS_CONFIG_TYPE: str = "app"

    class ClassConfigModel(BaseModel):
        app_name: str = "base"
        enabled_sprites: List[str] = ["web_sprite"]

    app_name: str
    secrets: Dict[str, str] = {}
    config: ClassConfigModel
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
            AppBase.update_app_config_file_from_default("base")
            AppBase.app_name = AppManager.load_web_sprite_default_app()
            if AppBase.app_name != "base":
                AppBase.update_app_config_file_from_default(AppBase.app_name)

        AppBase.local_index_dir = f"apps/{AppBase.app_name}/index"
        AppBase.app_dir = f"apps/{AppBase.app_name}/"
        load_dotenv(os.path.join(AppBase.app_dir, ".env"))
        AppBase.log = AppBase.get_logger(logger_name=AppBase.app_name)

        AppBase.create_app_enabled_instances(AppBase.app_name)

    @staticmethod
    def update_app_config_file_from_default(app_name):
        app_config_dict = AppManager.load_app_file(app_name)

        app_config_dict.setdefault(AppBase.CLASS_CONFIG_TYPE, {})
        (
            _,
            app_class_dict,
        ) = AppBase.load_class_config_model(
            class_config=AppBase.ClassConfigModel,
            class_config_dict=app_config_dict[AppBase.CLASS_CONFIG_TYPE],
        )
        app_config_dict[AppBase.CLASS_CONFIG_TYPE] = app_class_dict

        app_config_dict.setdefault(IndexBase.CLASS_CONFIG_TYPE, {})
        (
            _,
            index_class_dict,
        ) = AppBase.load_class_config_model(
            class_config=IndexBase.IndexConfigModel,
            class_config_dict=app_config_dict[IndexBase.CLASS_CONFIG_TYPE],
        )
        app_config_dict[IndexBase.CLASS_CONFIG_TYPE] = index_class_dict

        list_of_sprite_classes = AppBase.get_sprites(AppBase.AVAILABLE_SPRITES)
        app_config_dict = AppBase.load_config_and_or_class_instances(
            available_classes=list_of_sprite_classes,
            existing_dict=app_config_dict,
        )

        AppManager.save_app_file(
            app_name=app_name, updated_app_config_dict=app_config_dict
        )

    @staticmethod
    def update_app_config_file_from_ui():
        app_config_dict = AppManager.load_app_file(AppBase.app_name)

        app_config_dict.setdefault(AppBase.CLASS_CONFIG_TYPE, {})
        (
            _,
            app_class_dict,
        ) = AppBase.load_class_config_model(
            existing_class_config=AppBase.config,
            class_config_dict=app_config_dict[AppBase.CLASS_CONFIG_TYPE],
        )
        app_config_dict[AppBase.CLASS_CONFIG_TYPE] = app_class_dict

        app_config_dict.setdefault(IndexBase.CLASS_CONFIG_TYPE, {})
        (
            _,
            index_class_dict,
        ) = AppBase.load_class_config_model(
            existing_class_config=AppBase.index,
            class_config_dict=app_config_dict[IndexBase.CLASS_CONFIG_TYPE],
        )
        app_config_dict[IndexBase.CLASS_CONFIG_TYPE] = index_class_dict

        list_of_sprite_classes = AppBase.get_sprites(AppBase.config.enabled_sprites)
        app_config_dict = AppBase.load_config_and_or_class_instances(
            available_classes=list_of_sprite_classes,
            existing_dict=app_config_dict,
            update_from_ui=True,
        )

        AppManager.save_app_file(
            app_name=AppBase.app_name, updated_app_config_dict=app_config_dict
        )

    @staticmethod
    def create_app_enabled_instances(app_name):
        app_config_dict = AppManager.load_app_file(app_name)

        (
            AppBase.config,
            _,
        ) = AppBase.load_class_config_model(
            class_config=AppBase.ClassConfigModel,
            class_config_dict=app_config_dict[AppBase.CLASS_CONFIG_TYPE],
        )
        (
            AppBase.index,
            _,
        ) = AppBase.load_class_config_model(
            class_config=IndexBase.IndexConfigModel,
            class_config_dict=app_config_dict[IndexBase.CLASS_CONFIG_TYPE],
        )

        list_of_sprite_classes = AppBase.get_sprites(AppBase.config.enabled_sprites)
        app_config_dict = AppBase.load_config_and_or_class_instances(
            available_classes=list_of_sprite_classes,
            existing_dict=app_config_dict,
            create_instances=True,
        )

    @staticmethod
    def get_sprites(list_of_sprite_names: List[str]):
        list_of_sprite_classes = []
        for sprite_name in list_of_sprite_names:
            match sprite_name:
                case "web_sprite":
                    from sprites.web.web_sprite import WebSprite

                    list_of_sprite_classes.append(WebSprite)
                case "discord_sprite":
                    from sprites.discord_sprite import DiscordSprite

                    list_of_sprite_classes.append(DiscordSprite)
                case "slack_sprite":
                    from sprites.slack_sprite import SlackSprite

                    list_of_sprite_classes.append(SlackSprite)
                case _:
                    print("oops")

        return list_of_sprite_classes

    @staticmethod
    def load_config_and_or_class_instances(
        available_classes: List[Type],
        parent_class_instance=None,
        existing_dict: Optional[Dict[str, Any]] = None,
        create_instances=False,
        update_from_ui=False,
    ) -> Dict[str, Any]:
        updated_dict = existing_dict or {}
        for current_class in available_classes:
            # Get the names of the classes naming scheme
            base_class = current_class.__bases__[0]
            current_class_name_type = getattr(
                base_class,
                "CLASS_NAME_TYPE",
            )
            current_class_config_type = getattr(
                base_class,
                "CLASS_CONFIG_TYPE",
            )
            current_class_model_type = getattr(
                base_class,
                "CLASS_MODEL_TYPE",
            )

            current_class_name = getattr(current_class, current_class_name_type)
            updated_dict.setdefault(current_class_config_type, {}).setdefault(
                current_class_name, {}
            )
            existing_class_dict = updated_dict[current_class_config_type].get(
                current_class_name, {}
            )

            # Gets the existing current_class_config_model from UI
            current_class_config_model = None
            if update_from_ui:
                current_class_config_model = getattr(current_class, "config", None)
                (
                    config_class_instance,
                    config_class_dict,
                ) = AppBase.load_class_config_model(  # type: ignore
                    class_config=None,
                    existing_class_config=current_class_config_model,
                    class_config_dict=existing_class_dict,
                )
                AppBase.set_secrets(current_class)
            # Or use the default model
            if update_from_ui is False or current_class_config_model is None:
                current_class_config_model = getattr(
                    current_class, current_class_model_type
                )
                (
                    config_class_instance,
                    config_class_dict,
                ) = AppBase.load_class_config_model(
                    class_config=current_class_config_model,
                    existing_class_config=None,
                    class_config_dict=existing_class_dict,
                )

            updated_class_dict = existing_class_dict | config_class_dict  # type: ignore

            updated_dict[current_class_config_type][current_class_name].update(
                updated_class_dict
            )

            current_class_instance = None
            if create_instances:
                current_class_instance = current_class()
                AppBase.set_secrets(current_class_instance)
                setattr(current_class_instance, "config", config_class_instance)  # type: ignore
                if parent_class_instance:
                    setattr(
                        parent_class_instance,
                        current_class_name,
                        current_class_instance,
                    )
                else:
                    setattr(AppBase, current_class_name, current_class_instance)

            available_child_class_types = getattr(
                base_class, "AVAILABLE_CLASS_TYPES", None
            )
            # Recurse if nested classes exist
            if available_child_class_types:
                for available_child_class_type in available_child_class_types:
                    available_child_classes = getattr(
                        current_class, available_child_class_type
                    )

                    child_class_dict = AppBase.load_config_and_or_class_instances(
                        available_classes=available_child_classes,
                        parent_class_instance=current_class_instance,
                        existing_dict=updated_class_dict,
                        create_instances=create_instances,
                        update_from_ui=update_from_ui,
                    )
                    updated_dict[current_class_config_type][current_class_name].update(
                        child_class_dict
                    )

        return updated_dict

    @staticmethod
    def load_class_config_model(
        class_config: Optional[Type[ConfigModelType]] = None,
        existing_class_config: Optional[ConfigModelType] = None,
        class_config_dict: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ConfigModelType, Dict[str, Any]]:
        if existing_class_config is None and class_config is None:
            raise ValueError("Must supply either class_config or existing_class_config")

        if existing_class_config:
            config_class_instance = existing_class_config
        elif class_config:
            if class_config_dict:
                config_class_instance = class_config(
                    **class_config_dict, extra="ignore"
                )
            else:
                config_class_instance = class_config()
        else:
            raise ValueError("Unhandled configuration setup error")

        return config_class_instance, config_class_instance.model_dump()

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
        if (
            hasattr(class_instance, "REQUIRED_SECRETS")
            and class_instance.REQUIRED_SECRETS
        ):
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
