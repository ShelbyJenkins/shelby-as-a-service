import concurrent.futures
from services.deployment_service.deployment_management import DeploymentManager
from models.service_models import ServiceBase
from models.service_models import DeploymentModel
from models.service_models import IndexModel
from services.sprites.local_sprite import LocalSprite


class DeploymentInstance(ServiceBase):
    
    model_ = DeploymentModel()
    required_sprites_ = [LocalSprite]
    
    def __init__(self, deployment_name, **kwargs):
        """Instantiates deployment.
        super().__init__() initializes ServiceBase. We then override the base defaults.
        setup_config sets sprites as instance attrs using their service_name from model.
        """
        super().__init__()


        existing_deployment_names = DeploymentManager.check_for_existing_deployments()

        if deployment_name not in existing_deployment_names:
            if "base" == deployment_name:
                DeploymentManager().create_deployment("base")
                existing_deployment_names = (
                    DeploymentManager.check_for_existing_deployments()
                )
            else:
                # Need to return here with error
                print(f"Deployment {deployment_name} not found.")
                
        if "base" == deployment_name:
            DeploymentManager().update_app_json_from_model(DeploymentInstance, "base")
            # In the case of local deployment we check for a default_local_deployment
            deployment_config = DeploymentManager.load_deployment_file(deployment_name)
            default_settings = (
                deployment_config
                .get("sprites", {})
                .get("local_sprite", {})
                .get("optional", {})
            )
            if default_settings.get("default_deployment_enabled") is True:
                default_local_deployment_name = default_settings.get(
                    "default_local_deployment_name", None
                )
                if (
                    default_local_deployment_name is not None
                    and default_local_deployment_name in existing_deployment_names
                ):
                    deployment_name = default_local_deployment_name
                else:
                    print(
                        f"Default deployment '{default_local_deployment_name}' not found. Loading 'base' instead."
                    )
        
        if deployment_name != "base":
                DeploymentManager().update_app_json_from_model(
                    DeploymentInstance, deployment_name
                )
                deployment_config = DeploymentManager.load_deployment_file(
                    deployment_name
                )
                
        self.deployment_name = deployment_name
        config_from_file = DeploymentManager.load_deployment_file(self.deployment_name)
        self.setup_config(config_from_file, **kwargs)
        
        

    def run(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for sprite_name in self.enabled_sprites:
                sprite = getattr(self, sprite_name)
                executor.submit(sprite.run_sprite())

        # Move
        # Adds enabled domains and their description to deployment
        # for domain, description in self.index_data_domains.items():
        #     if domain in config_module.DeploymentConfig.enabled_data_domains:
        #         self.deployment_data_domains[domain] = description

