import concurrent.futures
import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
from services.utils.app_management import AppManager


class AppBase:
    
    service_name_ = "app_instance"
    
    # Set by setup_app_instance
    app_name: Optional[str] = None
    sprite: Optional[str] = None
    index_service: Optional[str] = None
    enabled_sprites: List[str] = []
    
    # Subclass instances shadow these
    config: Dict[str, str] = {}
    config_path: List[str] = []
    
    # Set by setup_instance_config 
    secrets: Dict[str, str] = {}
    required_secrets: List[str] = []
    
    total_cost: float = 0

    def __init__(
        self,
        service_name_,
        required_variables_=None,
        required_secrets_=None,
        config_path=None
    ):
        # Set subclass attrs
        self.service_name_ = service_name_
        self.required_variables_ = required_variables_
        self.required_secrets_ = required_secrets_
        
        if config_path:
            # Create copy rather than overwriting with the parent's copy
            config_path = config_path.copy()
            config_path.extend(['services', service_name_])
            self.config_path = config_path
            
            # Create a copy of the base config, and path to the config
            config = AppBase.config.copy()
            for path in self.config_path:
                config = config.get(path, None)
                if config is None:
                    break
        else:
            config = None
        
        AppBase.setup_service_from_config(self, config)
        self.config = config
        

    @staticmethod
    def setup_app_instance(app_name):
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

        AppBase.app_name = app_name

        # if app_name != "base":
        #     AppManager().update_app_json_from_file(cls, app_name)

        load_dotenv(os.path.join(f"apps/{AppBase.app_name}/", ".env"))
        
        from services.sprites.local_sprite import LocalSprite
        from services.index.index_service import IndexService
        
        AppBase.config = AppManager.load_app_file(AppBase.app_name)
        AppBase.config_path = ["app_instance"]
        
        # Index_service needs to init first
        AppBase.index_service = IndexService(AppBase.config_path)
        
        AppBase.sprite = LocalSprite(AppBase.config_path)
        
        # Check secrets
        for secret in AppBase.required_secrets:
            if AppBase.secrets.get(secret, None) is None:
                print(f"Secret: {secret} is None!")
    
    @staticmethod
    def setup_service_from_config(instance, config, from_file=True):
        
        # from_file overwrites class vars from file
        if from_file:
            config = {**vars(instance), **(config or {})}
        else:
            config = {**(config or {}), **vars(instance)}

        if hasattr(instance, 'required_secrets_') and instance.required_secrets_:
            for secret in instance.required_secrets_:
                secret_str = f"{instance.app_name}_{secret}".upper()
                env_secret = os.environ.get(secret_str)

                AppBase.secrets[secret] = env_secret
                AppBase.required_secrets.append(secret)

        # Removes services object used to structure the json file
        if config.get("services", None):
            config.pop("services")

        for key, value in config.items():
            setattr(instance, key, value)
            
    
    def set_provider(self, enabled_provider, enabled_model=None, config_path = None):
        used_provider = None
        default_provider = None
        for provider in self.available_providers:
            if enabled_model:
                provider = provider(config_path=config_path, enabled_model=enabled_model)
            else:
                provider = provider(config_path=config_path)
            setattr(self, provider.service_name_, provider)
            if provider.service_name_ == enabled_provider:
                used_provider = provider
            if provider.service_name_ == self.default_provider:
                default_provider = provider
        if used_provider:
            return used_provider
        else:
            return default_provider
    
    def set_model(self, enabled_model):
        if enabled_model not in [model.model_name for model in self.available_models]:
            enabled_model = self.default_model
        for model in self.available_models:
            if model.model_name == enabled_model:
                return model
        return None
    

        
    # def run_sprites(self):

    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     for sprite_name in self.enabled_sprites:
    #         sprite = getattr(self, sprite_name)
    #         executor.submit(sprite.run_sprite())
