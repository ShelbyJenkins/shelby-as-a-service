import concurrent.futures
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from services.utils.app_management import AppManager


class AppBase:
    app_name: Optional[str] = None
    sprite: Optional[str] = None
    index_service: Optional[str] = None
    service_name_ = "app_instance"
    secrets: Dict[str, str] = {}
    total_cost: float = 0

    def __init__(
        self,
        service_name_,
        required_variables_=None,
        required_secrets_=None,
        config=None,
    ):
        self.service_name_ = service_name_
        self.required_variables_ = required_variables_
        self.required_secrets_ = required_secrets_
        self.setup_config(config)

    @classmethod
    def setup_app_instance(cls):
        # existing_app_names = AppManager.check_for_existing_apps()

        # if cls.app_name not in existing_app_names:
        #     if "base" == cls.app_name:
        #         AppManager().create_app("base")
        #         existing_app_names = AppManager.check_for_existing_apps()
        #     else:
        #         # Need to return here with error
        #         print(f"app {cls.app_name} not found.")

        # if "base" == cls.app_name:
        #     AppManager().update_app_json_from_file(cls, "base")
        #     # In the case of local app we check for a default_local_app
        #     app_config = AppManager.load_app_file(cls.app_name)
        #     default_settings = (
        #         app_config.get("sprites", {})
        #         .get("local_sprite", {})
        #         .get("optional", {})
        #     )
        #     if default_settings.get("default_app_enabled") is True:
        #         default_local_app_name = default_settings.get(
        #             "default_local_app_name", None
        #         )
        #         if (
        #             default_local_app_name is not None
        #             and default_local_app_name in existing_app_names
        #         ):
        #             app_name = default_local_app_name
        #         else:
        #             print(
        #                 f"Default app '{default_local_app_name}' not found. Loading 'base' instead."
        #             )

        # cls.app_name = app_name

        # if app_name != "base":
        #     AppManager().update_app_json_from_file(cls, app_name)

        load_dotenv(os.path.join(f"apps/{cls.app_name}/", ".env"))

        return AppManager.load_app_file(cls.app_name).get("app_instance", None)
        

    def setup_config(self, config):
        # Main app instance
        model_dict = vars(self)
        config = {**model_dict, **(config or {})}

        if self.required_secrets_:
            for secret in self.required_secrets_:
                secret_str = f"{self.app_name}_{secret}".upper()
                env_secret = os.environ.get(secret_str)
                if not env_secret:
                    print(f"Secret: {secret_str} is None!")
                AppBase.secrets[secret] = env_secret

        # Removes services object used to structure the json file
        if config.get("services", None):
            config.pop("services")

        for key, value in config.items():
            setattr(self, key, value)

    # def run_sprites(self):

    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     for sprite_name in self.enabled_sprites:
    #         sprite = getattr(self, sprite_name)
    #         executor.submit(sprite.run_sprite())
