import os
import requests
import json
import sys
import time
from importlib import import_module

def main(deployment_name):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

    url = "https://gateway.stackpath.com/identity/v1/oauth2/token"

    # Load secrets
    required_secrets_list = os.environ.get("REQUIRED_SECRETS", "").split(";")
    client_id = os.environ.get(f"{deployment_name.upper()}_STACKPATH_CLIENT_ID")
    client_secret = os.environ.get(f"{deployment_name.upper()}_STACKPATH_API_CLIENT_SECRET")
    stack_slug = os.environ.get(f"{deployment_name.upper()}_STACKPATH_STACK_SLUG")
    # Load config
    config_module_path = f"deployments.{deployment_name}.deployment_config"
    config = import_module(config_module_path)
    # Generate deployment vars
    workload_name = f"{deployment_name}-workload"
    slug_name = f"{deployment_name}-slug"
    docker_image_path = f"{config.DeploymentConfig.docker_username}/{config.DeploymentConfig.docker_repo}:{deployment_name}-latest"
    docker_server = f"{config.DeploymentConfig.docker_registry}/{config.DeploymentConfig.docker_username}/{config.DeploymentConfig.docker_repo}"

    headers = {"accept": "application/json", "content-type": "application/json"}
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response = requests.post(url, json=payload, headers=headers)
    bearer_token = json.loads(response.text)["access_token"]
    if response.status_code == 200 and bearer_token:
        print("Got bearer token.")
    else:
        raise ValueError("Did not get workloads.")

    url = f"https://gateway.stackpath.com/stack/v1/stacks/{stack_slug}"
    headers = {"accept": "application/json", "authorization": f"Bearer {bearer_token}"}

    response = requests.get(url, headers=headers)
    stack_id = json.loads(response.text)["id"]
    if response.status_code == 200 and stack_id:
        print(f"Got stack_id: {stack_id}")
    else:
        raise ValueError("Did not get stack_id.")

    # Get existing workloads
    # And delete an existing workload with the same name as the one we're trying to deploy
    url = f"https://gateway.stackpath.com/workload/v1/stacks/{stack_id}/workloads"
    response = requests.get(url, headers=headers)
    workloads = response.json()
    workloads = workloads.get("results")
    if response.status_code == 200:
        print(f"Got workloads: {len(workloads)}")
    else:
        raise ValueError("Did not get workloads.")
    for workload in workloads:
        print(f'Existing workload name: {workload["name"]}')
        if workload["name"] == workload_name:
            workload_id = workload["id"]
            url = f"https://gateway.stackpath.com/workload/v1/stacks/{stack_id}/workloads/{workload_id}"
            response = requests.delete(url, headers=headers)
            if response.status_code == 204:
                print("workload deleted")
                time.sleep(5)
                
    # Load configuration from JSON file
    with open(
        "app/deployment_maker/sp-2_container_request_template.json", "r", encoding="utf-8"
    ) as f:
        request_template = json.load(f)

    # Add env vars to the environment variables of the container
    request_template["payload"]["workload"]["spec"]["containers"]["webserver"][
        "image"
    ] = docker_image_path
    request_template["payload"]["workload"]["spec"]["imagePullCredentials"][0]["dockerRegistry"][
        "server"
    ] = docker_server
    request_template["payload"]["workload"]["spec"]["imagePullCredentials"][0]["dockerRegistry"][
        "username"
    ] = config.DeploymentConfig.docker_username
    request_template["payload"]["workload"]["spec"]["imagePullCredentials"][0]["dockerRegistry"][
        "password"
    ] = os.environ.get(f"{deployment_name.upper()}_DOCKER_TOKEN")

    request_template["payload"]["workload"]["name"] = workload_name
    request_template["payload"]["workload"]["slug"] = slug_name

    if "env" not in request_template["payload"]["workload"]["spec"]["containers"]["webserver"]:
        request_template["payload"]["workload"]["spec"]["containers"]["webserver"]["env"] = {}

    for secret in required_secrets_list:
        var = f"{deployment_name.upper()}_{secret.upper()}"
        val = os.environ.get(var)
        request_template["payload"]["workload"]["spec"]["containers"]["webserver"]["env"].update(
            {var: {"secretValue": val}}
        )

    print(request_template)
    url = f"https://gateway.stackpath.com/workload/v1/stacks/{stack_slug}/workloads"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {bearer_token}",
    }
    payload = request_template["payload"]
    
    # Define a timeout value (in seconds)
    timeout = 5
    # Make the API call
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code == 200:
            print(f"{workload_name} created : {response.text}")
        else:
            print(f"Something went wrong creating the workload: {response.text}")
    except requests.Timeout as t:
        print("Request timed out: ", t)
