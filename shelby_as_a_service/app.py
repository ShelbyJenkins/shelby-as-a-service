import argparse

from models.app_base import AppBase
from services.sprites.local_sprite import LocalSprite
from services.index.index_service import IndexService


def create_app(app_name):

    AppBase.app_name = app_name
    config = AppBase.setup_app_instance()
    AppBase.sprite = LocalSprite(config)
    AppBase.index_service = IndexService(config)
    AppBase.sprite.run_sprite()


def main():
    """
    This script runs shelby-as-a-service when deployed to a container.
    AND
    When running locally.

    Usage:
        None. Deployment will be configured via automation.
        If ran without args, local_web is ran.
    """
    print(f"app.py is being run as: {__name__}")

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--run_container_deployment",
        type=str,
        help="This will be called from the dockerfile after the container deploys.",
    )
    group.add_argument(
        "--deploy_container",
        type=str,
        help="This will be called from the github actions workflow to deploy the container.",
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
        deployment = create_app(app_name="base")


if __name__ == "__main__":
    main()
