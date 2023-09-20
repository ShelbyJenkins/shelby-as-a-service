import concurrent.futures
import os
from dataclasses import asdict
from dotenv import load_dotenv
from services.apps.app_management import AppManager


class AppBase:
    
    app = None
    app_name = None
    secrets = {}

    def setup_app_instance(self, app):
        app_name = app.app_name
        AppBase.app = app

        existing_app_names = AppManager.check_for_existing_apps()

        if app_name not in existing_app_names:
            if "base" == app_name:
                AppManager().create_app("base")
                existing_app_names = AppManager.check_for_existing_apps()
            else:
                # Need to return here with error
                print(f"app {app_name} not found.")
        
        if "base" == app_name:
            AppManager().update_app_json_from_model(self, "base")
            # In the case of local app we check for a default_local_app
            app_config = AppManager.load_app_file(app_name)
            default_settings = (
                app_config.get("sprites", {})
                .get("local_sprite", {})
                .get("optional", {})
            )
            if default_settings.get("default_app_enabled") is True:
                default_local_app_name = default_settings.get(
                    "default_local_app_name", None
                )
                if (
                    default_local_app_name is not None
                    and default_local_app_name in existing_app_names
                ):
                    app.app_name = default_local_app_name
                else:
                    print(
                        f"Default app '{default_local_app_name}' not found. Loading 'base' instead."
                    )

        if app_name != "base":
            AppManager().update_app_json_from_model(self, app_name)

        load_dotenv(os.path.join(f"apps/{app_name}/", ".env"))
        # AppBase.load_index(app)

    def setup_sprites(self):
        if hasattr(self, "required_sprites_"):
            for sprite in self.required_sprites_:
                sprite_instance = sprite()
                setattr(self, sprite.model_.service_name_, sprite_instance)

    def setup_services(self):
        if hasattr(self, "required_services_") and self.required_services_ is not None:
            for service in self.required_services_:
                service_instance = service()
                setattr(self, service.model_.service_name_, service_instance)

    def setup_config(self):
        if self.model_ is None:
            print(f"RNR: {self.model_} not found in {self}!")
            return None

        config_from_file = AppManager.load_app_file(self.app.app_name)
        service_config = config_from_file.get(self.model_.service_name_, None)

        if service_config is None:
            print(f"RNR: {self.model_.service_name_} not found in config_from_file!")
            config = {**asdict(self.model_)}
        else:
            config = {**asdict(self.model_), **service_config}

        if config.get("services", None):
            config.pop("services")

        for key, value in config.items():
            setattr(self, key, value)

        if hasattr(self.model_, "required_secrets_"):
            self._load_secrets(self.model_)

    def _load_secrets(self, model):
        for secret in model.required_secrets_:
            secret_str = f"{self.app.app_name}_{secret}"
            secret_str = secret_str.upper()
            env_secret = os.environ.get(secret_str, None)
            if env_secret in [None, ""]:
                print(f"Secret: {secret_str} is None!")
            AppBase.secrets[secret] = env_secret

    def run_sprites(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in self.enabled_sprites:
                sprite = getattr(self, sprite_name)
                executor.submit(sprite.run_sprite())
