import sys
import argparse
from importlib import import_module
from app.services.deployment_instantiator import DeploymentInstance

def main():
    """
    This script runs shelby-as-a-serice when deployed to a container.
    AND
    When running locally.

    Usage:
        None. Deployment will be configured via automation.
        If ran with our args, local_web is ran.
    """
    print(f"app.py is being run as: {__name__}")

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--run_container_deployment",
        help="This will be called from the dockerfile after the container deploys.",
    )
    group.add_argument(
        "--deploy_container",
        help="This will be called from the github actions workflow to deploy the container.",
    )
    
    if len(sys.argv) > 1:
        args = parser.parse_args(sys.argv[1:])
        if args.run_container_deployment:
            deployment_name = args.run_container_deployment
            config_module_path = f"deployments.{deployment_name}.deployment_config"
            config_module = import_module(config_module_path)
            deployment = DeploymentInstance(config_module)
            deployment.run()
        elif args.deploy_container:
            deployment_name = args.deploy_container
            deploy_stackpath_container.main(deployment_name)
    else:
        deployment = DeploymentInstance('base') 
        deployment.run()

if __name__ == "__main__":
    main()
