import concurrent.futures
import os
from dataclasses import replace, is_dataclass, asdict
from dotenv import load_dotenv
from services.apps.app_management import AppManager


class AppBase:
    """Base model for all services.
    Child classes have access to all class variables of AppBase with self.variable.
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
                    app_name = default_local_app_name
                else:
                    print(
                        f"Default app '{default_local_app_name}' not found. Loading 'base' instead."
                    )

        app.app_name = app_name
        AppBase.app_name = app_name
        
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
            has_model = hasattr(self, 'model_')
            if not has_model:
                print(f"No model found for {self}")
            if config is None:
                print(f"No config found for {self}")
            if not config and not has_model:
                print(f"No config or model found for {self}")
                return None

            model_dict = asdict(self.model_) if has_model else {}
            config = {**model_dict, **(config or {})}
    
    
            if hasattr(self.model_, "required_secrets_"):
                for secret in self.model_.required_secrets_:
                    secret_str = f"{self.app.app_name}_{secret}".upper()
                    env_secret = os.environ.get(secret_str)
                    if not env_secret:
                        print(f"Secret: {secret_str} is None!")
                    AppBase.secrets[secret] = env_secret
                    
        
        if hasattr(self, "required_services_") and self.required_services_:
            services_config = config.get("services", None)
            if services_config is None:
                print("Error loading from file!")
                return None
            for service in self.required_services_:
                service_name = service.model_.service_name_
                service_instance = service()
                service_instance.setup_config(services_config.get(service_name))
                setattr(self, service_name, service_instance)
   
        # Removes services object used to structure the json file
        if config.get("services", None):
            config.pop("services")
    
        for key, value in config.items():
            setattr(self, key, value)
            
        if getattr(getattr(self, 'model_', None), 'service_name_', None) == "index_service":
            self.load_index_model_as_dataclasses(self.model_, config)
    
    def load_index_model_as_dataclasses(self, index_model, config):
        
        def merge_attributes(obj, config):
            # If obj is a list of dataclass instances
            if isinstance(obj, list) and obj and is_dataclass(obj[0]):
                obj = obj[0]

            replacements = {}
            # Process each attribute of the dataclass instance
            for key, val in vars(obj).items():
                config_value = config.get(key)

                # If val is a list of dataclass instances
                if isinstance(val, list) and val and is_dataclass(val[0]):
                    item_configs = config_value if isinstance(config_value, list) else [{}]
                    replacements[key] = [merge_attributes(val_item, item_config) for val_item, item_config in zip(val, item_configs)]
                
                elif AppManager.check_for_ignored_objects(key):
                    if config_value is not None:
                        replacements[key] = config_value

            return replace(obj, **replacements)

        config = config or {}
        index_instances_config = config.get('index_instances', [])
        merged_index_instances = [
            merge_attributes(index_model.index_instances, instance)
            for instance in index_instances_config or [{}]
        ]
        setattr(self, 'index_instances', merged_index_instances)
        
                                    
    def run_sprites(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in self.enabled_sprites:
                sprite = getattr(self, sprite_name)
                executor.submit(sprite.run_sprite())
