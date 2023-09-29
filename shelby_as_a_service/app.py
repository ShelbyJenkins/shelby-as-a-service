import argparse
import concurrent.futures
import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
import modules.utils.app_manager as AppManager
import modules.utils.config_manager as ConfigManager
from modules.utils.log_service import Logger



class AppBase:
    
    app_manager = AppManager
    config_manager = ConfigManager
    app_config_path: str = "app_instance"
    index_config_path: str = "index"
    sprite_config_path: str = "services" # Change to sprites
    agent_config_path: str = "services" # Change to agents
    service_config_path: str = "services" # Change to services
    provider_config_path: str = "services" # Change to providers

    # Set during run
    total_cost_: float = 0
        
    def setup_app(self, app_name):
        AppBase.app = self
        AppBase.app.secrets: Dict[str, str] = {}
        AppBase.app.required_secrets: List[str] = []
        
        AppBase.app.log = Logger(
            app_name,
            app_name,
            f"{app_name}.md",
            level="INFO",
        )
        
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
        
        AppBase.app.log = Logger(
            AppBase.app.app_name,
            AppBase.app.app_name,
            f"{AppBase.app.app_name}.md",
            level="INFO",
        )
        # if app_name != "base":
        #     AppManager().update_app_json_from_file(cls, app_name)

        load_dotenv(os.path.join(f"apps/{AppBase.app_name}/", ".env"))

        from sprites.local.local_sprite import LocalSprite
        from modules.index_service import IndexService

        AppBase.config = AppBase.app_manager.load_app_file(AppBase.app_name)
        
        # Index needs to init first
        AppBase.app.index = IndexService(AppBase.app)

        AppBase.app.local_sprite = LocalSprite(AppBase.app)

        # Check secrets
        for secret in AppBase.app.required_secrets:
            if AppBase.app.secrets.get(secret, None) is None:
                print(f"Secret: {secret} is None!")
        

    # def run_sprites(self):

    #     # with concurrent.futures.ThreadPoolExecutor() as executor:
        
    #     for sprite_name in self.enabled_sprites:
    #         sprite = getattr(self, sprite_name)
    #         executor.submit(sprite.run_sprite())

    
def main():
    """
    This script runs shelby-as-a-service when deployed to a container.
    AND
    When running locally.

    Usage:
        None. Deployment is configured via automation.
        If ran without args, local_web is ran.
    """
    print(f"app.py is being run as: {__name__}")

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--run_container_deployment",
        type=str,
        help="This is called from the dockerfile after the container deploys.",
    )
    group.add_argument(
        "--deploy_container",
        type=str,
        help="This is called from the github actions workflow to deploy the container.",
    )
    parser.add_argument(
        "deployment_name",
        type=str,
        nargs="?",
        help="For local deployment provide the name of the deployment.",
    )
    args = parser.parse_args()

    if args.run_container_deployment:
        deployment = AppInstance(args.run_container_deployment)
        deployment.run_sprites()
    elif args.deploy_container:
        deploy_container(args.deploy_container)
    elif args.deployment_name:
        deployment = AppInstance(args.deployment_name)
        deployment.run_sprites()
    else:
        AppBase().setup_app(app_name='base')
        AppBase.app.local_sprite.run_sprite()

if __name__ == "__main__":
    main()
