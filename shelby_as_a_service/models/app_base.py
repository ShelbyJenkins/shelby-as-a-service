import concurrent.futures
import os
from dataclasses import asdict
from dotenv import load_dotenv
from services.apps.app_management import AppManager


class AppBase:
    """Base model for all services.
    Child classes have access to all class variables of ServiceBase with self.variable.
    setup_config uses asdict to load settings from models, configs, and function params.
    It then loads child services by passing a config file and instantiating the service.
    """
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
            AppManager().update_app_json_from_file(self, "base")
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
            AppManager().update_app_json_from_file(self, app_name)

        load_dotenv(os.path.join(f"apps/{app_name}/", ".env"))
        
        self.setup_config(AppManager.load_app_file(app_name))


    def setup_config(self, config=None):
        
        # Main app instance
        if getattr(self, 'service_name_', None) == 'app_instance':
            config = config.get('app_instance', None)
        # All other services
        else:
            if config is None and not hasattr(self, 'model_'):
                print(f"No config or model found for {self}")
                return None
            elif not hasattr(self, 'model_'):
                    print(f"No model found for {self}")
            elif config is None:
                print(f"No config found for {self}")
                config = {**asdict(self.model_)}
            else:
                config = {**asdict(self.model_), **config}
    
            if hasattr(self.model_, "required_secrets_"):
                for secret in self.model_.required_secrets_:
                    secret_str = f"{self.app.app_name}_{secret}"
                    secret_str = secret_str.upper()
                    env_secret = os.environ.get(secret_str, None)
                    if env_secret in [None, ""]:
                        print(f"Secret: {secret_str} is None!")
                    AppBase.secrets[secret] = env_secret
        
        if hasattr(self, "required_services_") and self.required_services_:
            services_config = config.get("services", None)
            if services_config is None:
                print("Error loading from file!")
                return None
            for service in self.required_services_:
                service_name = service.model_.service_name_
                service_config = services_config.get(service_name, None)
                service_instance = service()
                service_instance.setup_config(service_config)
                setattr(self, service_name, service_instance)
                
        # if hasattr(self, "required_sprites_") and self.required_sprites_:
        #     sprites_config = config.get("services", None)
        #     if sprites_config is None:
        #         print("Error loading from file!")
        #         return None
        #     for sprite in self.required_sprites_:
        #         sprite_name = sprite.model_.service_name_
        #         sprite_config = sprites_config.get(sprite_name, None)
        #         sprite_instance = sprite()
        #         sprite_instance.setup_config(sprite_config)
        #         setattr(self, sprite_name, sprite_instance)
                

        # Removes services object used to structure the json file
        if config.get("services", None):
            config.pop("services")
    
        for key, value in config.items():
            setattr(self, key, value)
    
    def run_sprites(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in self.enabled_sprites:
                sprite = getattr(self, sprite_name)
                executor.submit(sprite.run_sprite())
