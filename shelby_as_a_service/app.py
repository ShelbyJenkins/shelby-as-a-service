import argparse

from services.utils.app_base import AppBase


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
        AppBase.setup_app_instance('base')
        AppBase.sprite.run_sprite()

if __name__ == "__main__":
    main()
