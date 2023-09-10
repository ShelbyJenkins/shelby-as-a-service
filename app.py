import sys
import argparse
from app.services.deployment_instantiator import DeploymentInstance
from app.services.deployment_service.deploy_stackpath_container import deploy_container

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
        nargs='?',
        help="For local deployment provide the name of the deployment.",
    )
    args = parser.parse_args()
   
    if args.run_container_deployment:
        deployment = DeploymentInstance(args.run_container_deployment)
        deployment.run()
    elif args.deploy_container: 
        deploy_container(args.deploy_container)
    elif args.deployment_name: 
        deployment = DeploymentInstance(args.deployment_name) 
        deployment.run()
    else:
        deployment = DeploymentInstance('base') 
        deployment.run()

if __name__ == "__main__":
    main()
