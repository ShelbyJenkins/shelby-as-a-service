import os
import concurrent.futures
import yaml
from dotenv import load_dotenv
from typing import List

from services.deployment_service.deployment_management import DeploymentManager
from models.service_models import ServiceBase
from models.service_models import DeploymentModel
from services.sprites.local_sprite import LocalSprite


class DeploymentInstance(ServiceBase):
    
    model = DeploymentModel()
    
    def __init__(self, deployment_name, **kwargs):
        """Instantiates deployment.
        super().__init__() initializes ServiceBase. We then override the base defaults.
        setup_config sets sprites as instance attrs using their service_name from model.
        """
        super().__init__()
        self.required_services = [LocalSprite]
        self.deployment_name = deployment_name
        self.setup_config(**kwargs)
        load_dotenv(os.path.join(f"app/deployments/{self.deployment_name}/", ".env"))
        
        # existing_deployment_names = DeploymentManager.check_for_existing_deployments()

        # if "base" == deployment_name:
        #     # if "base" not in existing_deployment_names:
        #     #     DeploymentManager().create_deployment(ServiceBase, "base")
        #     #     existing_deployment_names = (
        #     #         DeploymentManager.check_for_existing_deployments()
        #     #     )
        #     # else:
        #     #     DeploymentManager().update_deployment_yaml(ServiceBase, "base")

        #     # In the case of local deployment we check for a default_local_deployment
        #     deployment_config = DeploymentManager.load_deployment_file(deployment_name)
        #     default_settings = (
        #         deployment_config["deployment_instance"]
        #         .get("sprites", {})
        #         .get("local_sprite", {})
        #         .get("optional", {})
        #     )
        #     if default_settings.get("default_deployment_enabled") is True:
        #         default_local_deployment_name = default_settings.get(
        #             "default_local_deployment_name", None
        #         )
        #         if (
        #             default_local_deployment_name is not None
        #             and default_local_deployment_name in existing_deployment_names
        #         ):
        #             deployment_name = default_local_deployment_name
        #             # print(f"Loading default deployment '{deployment_name}'.")
        #             # DeploymentManager().update_deployment_yaml(
        #             #     DeploymentInstance, deployment_name
        #             # )
        #             # deployment_config = DeploymentManager.load_deployment_file(
        #             #     default_local_deployment_name
        #             # )
        #         else:
        #             print(
        #                 f"Default deployment '{default_local_deployment_name}' not found. Loading 'base' instead."
        #             )

        #     self.deployment_name = deployment_name
        #     # self.load_local_sprite_deployment(deployment_config = deployment_config)
        #     self.load()
            
        # else:
        #     if deployment_name not in existing_deployment_names:
        #         # Need to return here with error
        #         print(f"Deployment {deployment_name} not found.")
        #     else:
        #         self.deployment_name: str = deployment_name
        #         DeploymentManager().update_deployment_yaml(
        #             DeploymentInstance, deployment_name
        #         )
        #         deployment_config = DeploymentManager.load_deployment_file(
        #             deployment_name
        #         )
                

        
    def _load_instance_from_models(self):
        for sprite_model in self.available_sprites_:
            sprite_class = sprite_model.sprite_class_(sprite_model)

            for k, v in sprite_model.__dict__.items():
                if not k.startswith("_") and not callable(v):
                    setattr(sprite_class, k, v)

            for service_model in sprite_model.required_services_:
                service_class = service_model.service_class_()
                for k, v in service_model.__dict__.items():
                    if not k.startswith("_") and not callable(v):
                        setattr(service_class, k, v)

                for secret in service_model.secrets_:
                    self.secrets.add(secret)

                setattr(sprite_class, service_class)

            for secret in sprite_model.secrets_:
                self.secrets.add(secret)

            setattr(self, sprite_class)

        # def _load_index(self, folder_path):
        #     with open(
        #         os.path.join(folder_path, "index_description.yaml"),
        #         "r",
        #         encoding="utf-8",
        #     ) as stream:
        #         index_description_file = yaml.safe_load(stream)

        #     # Iterate over each domain in the yaml file
        #     for domain in index_description_file["data_domains"]:
        #         self.index_data_domains[domain["name"]] = domain["description"]

        #     self.index_name: str = index_description_file["index_name"]
        #     self.index_env: str = index_description_file["index_env"]

        # def _load_index_agent(self):
        self.index_config = IndexModel()
        for secret in self.index_config.SECRETS_:
            self.secrets[secret] = os.environ.get(
                f"{self.deployment_name.upper()}_{secret.upper()}"
            )
        return IndexService(self)
        
    def load_local_sprite_deployment(self, deployment_config, deployment_name = None):
 
            
        deployment_folder_path = f"app/deployments/{deployment_name}/"

        load_dotenv(os.path.join(deployment_folder_path, ".env"))

        if (
            deployment_config.get("deployment_instance", None) is None
            or deployment_config.get("deployment_instance", {}).get("sprites", None)
            is None
        ):
            raise ValueError(
                "The keys 'deployment_instance' and 'sprites' should not be None"
            )

        # Deployment
        deployment_instance_config = deployment_config["deployment_instance"]
        self.config = self.load_classes_and_configs(
            DeploymentInstance.model_, deployment_instance_config
        )

        # Sprites
        sprites_config = deployment_instance_config["sprites"]

        # Sprite
        for sprite_class in self.available_sprites_:
            sprite_model = sprite_class.model_
            sprite_name_model = sprite_model.sprite_name_

            if sprite_name_model in self.config.enabled_sprites:
                sprite_config = sprites_config[sprite_name_model]
                sprite_model = self.load_classes_and_configs(
                    sprite_model(), sprite_config
                )

                # Services
                service_classes = []
                for service_class in sprite_class.required_services_:
                    service_model = service_class.model_
                    service_class_name = service_model.service_name_

                    # Service
                    service_config = sprite_config["services"][service_class_name]
                    service_model = self.load_classes_and_configs(
                        service_model(), service_config
                    )
                    service_classes.append(service_class(self, service_model))

                instantiated_sprite = sprite_class(self, sprite_model, service_classes)
                self.sprites.append(instantiated_sprite)

    def load_classes_and_configs(self, model_class, config):
        """s"""
        for var, value in vars(model_class).items():  # sort by variable name
            if (
                not var.startswith("_")
                and not var.endswith("_")
                and not callable(value)
            ):
                if var in model_class.required_variables_:
                    required_dict = config.get("required")
                    if not required_dict or required_dict.get(var) in [None, ""]:
                        # raise ValueError(f"Required variable {var} can not be None")
                        continue
                    else:
                        setattr(model_class, var, required_dict[var])
                else:
                    optional_dict = config.get("optional")
                    if not optional_dict or optional_dict.get(var) in [None, ""]:
                        continue
                    else:
                        setattr(model_class, var, optional_dict[var])

        for secret_key in model_class.secrets_:
            secret_value = os.environ.get(
                f"{self.deployment_name.upper()}_{secret_key.upper()}"
            )
            self.secrets[secret_key] = secret_value

        return model_class

    def check_secrets(self, model_secrets):
        """For disabling services lacking secrets"""
        for secret in model_secrets:
            if not self.secrets.get(secret):
                return False

        return True

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
