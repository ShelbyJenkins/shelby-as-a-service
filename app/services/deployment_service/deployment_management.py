import os
import sys
import textwrap
import inspect
import shutil
from importlib import import_module
import yaml

class DeploymentManager:
    def __init__(self):
        pass

        # Exits here on first run

        # # secrets from sprites, and deployment
        # self.used_sprites = set()
        # self.required_secrets = set()
        # self.required_deployment_vars = {}
        # config_module_path = f"deployments.{deployment_name}.deployment_config"
        # self.config = import_module(config_module_path)
        # self.load_moniker_requirments()
        # self.load_deployment_requirments()
        # self.generate_dockerfile()
        # self.generate_pip_requirements()
        # self.generate_actions_workflow()

    @staticmethod
    def check_for_existing_deployments():
        
        existing_deployment_names = []
        for deployment in os.listdir("app/deployments"):
            deployment_path = os.path.join("app/deployments", deployment)
            if os.path.isdir(deployment_path):
                if "deployment_config.yaml" in os.listdir(deployment_path):
                    existing_deployment_names.append(deployment)
                    
        return existing_deployment_names
    
    @staticmethod
    def load_deployment_file(deployment_name, service_name):
        
        with open(
            f"app/deployments/{deployment_name}/deployment_config.yaml",
            "r",
            encoding="utf-8",
        ) as stream:
            config_from_file = yaml.safe_load(stream)
            
        return config_from_file[service_name]
    
    def create_deployment(self, deployment_instance, deployment_name):
        """Creates a new deployment by copying from the template folder.
        Does not overwrite existing deployments.
        To start fresh delete the deployment and then use this function.
        """
        dir_path = f"app/deployments/{deployment_name}"
        
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if not os.path.exists(os.path.join(dir_path, "index/inputs")):
            os.makedirs(os.path.join(dir_path, "index/inputs"))
        
        # Creates blank deployment_config.yaml
        deployment_config_dest_path = os.path.join(dir_path, "deployment_config.yaml")
        if not os.path.exists(deployment_config_dest_path):
            with open(deployment_config_dest_path, 'w', encoding='utf-8') as file:
                pass
            # Adds variables to config file from models
            self.update_deployment_yaml(deployment_instance, deployment_name)
            
        index_description_dest_path = os.path.join(dir_path, "index_description.yaml")
        if not os.path.exists(index_description_dest_path):
            index_description_source_path = "app/services/deployment_service/template/index_description.yaml"
            shutil.copy(index_description_source_path, index_description_dest_path)

        dot_env_dest_path = os.path.join(dir_path, ".env")
        if not os.path.exists(dot_env_dest_path):
            dot_env_source_path = "app/services/deployment_service/template/template.env"    
            with open(dot_env_source_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                modified_lines = []
                for line in lines:
                    # If the line starts with a comment or is empty, keep it unchanged
                    if line.startswith("#") or line.strip() == "":
                        modified_lines.append(line)
                    else:
                        modified_lines.append(f"{deployment_name.upper()}_{line}")
       
            with open(dot_env_dest_path, 'w', encoding='utf-8') as file:
                file.writelines(modified_lines)
    
    def update_deployment_yaml(self, deployment_instance, deployment_name):
        """Populates deployment_config.py from models.
        If the existing deployment_config.py has existing values it does not overwrite them.
        """
        
        deployment_config_file = DeploymentManager.load_deployment_file(deployment_name)

        if deployment_config_file is None:
            deployment_config_file = {}
        
        # Deployment
        if 'deployment_instance' not in deployment_config_file:
            deployment_instance_config = {}
        else:
            deployment_instance_config = deployment_config_file['deployment_instance']
            
        deployment_instance_config = self.load_variables_as_dicts(deployment_instance.model_, deployment_instance_config)
        
        # Sprites
        if 'sprites' not in deployment_instance_config:
            sprites_config = {}
        else:
            sprites_config = deployment_instance_config['sprites']
        
        # Sprite
        for sprite_class in deployment_instance.available_sprites_:
            sprite_model = sprite_class.model_
            sprite_name_model = sprite_model.sprite_name_
            if sprite_name_model not in sprites_config:
                sprite_config = {}
            else:
                sprite_config = sprites_config[sprite_name_model]
                
            sprite_config = self.load_variables_as_dicts(sprite_model, sprite_config)
            
            # Services
            if 'services' not in sprite_config:
                sprite_config['services'] = {}
                services_config = {}
            else:
                services_config = sprite_config['services']
                
            for sprite_class_required_service in sprite_class.required_services_:
                service_model =  sprite_class_required_service.model_
                service_class_name = service_model.service_name_
                
                # Service
                if service_class_name not in services_config:
                    service_config = {}
                else:
                    service_config = services_config[service_class_name]
                
                service_config = self.load_variables_as_dicts(service_model, service_config)

                sprite_config['services'][service_class_name] = service_config
                
            sprites_config[sprite_name_model] = sprite_config
            
        deployment_instance_config['sprites'] = sprites_config
        deployment_config_file['deployment_instance'] = deployment_instance_config
            
        # Save the updated configuration
        with open(f"app/deployments/{deployment_name}/deployment_config.yaml", "w", encoding="utf-8") as stream:
            yaml.safe_dump(deployment_config_file, stream)
            
    def load_variables_as_dicts(self, model_class, config):
        """Loads variables and values from models and existing deployment_config.py.
        Adds variables from models if they don't exist in deployment_config.py.
        If values exist for variables in deployment_config.py it uses those.
        """
        if not config.get('required'):
            config['required'] = {}
        # Handle 'required'
        for var, value in sorted(vars(model_class).items()):  # sort by variable name
            if not var.startswith("_") and not var.endswith("_") and not callable(value):
                if var in model_class.required_variables_:
                    if config['required'].get(var) in [None, '']:
                        config['required'][var] = value
                    else:
                        continue
                        
        if not config.get('optional'):
            config['optional'] = {}
        # Handle 'optional'
        for var, value in sorted(vars(model_class).items()):  # sort by variable name
            if not var.startswith("_") and not var.endswith("_") and not callable(value):
                if var not in model_class.required_variables_:
                    if config['optional'].get(var) in [None, '']:
                        config['optional'][var] = value
                    else:
                        continue
                        # config['optional'][var] = config['optional'].get(var)
                        

        return config
          
    def load_moniker_requirments(self):
        for moniker in self.config.DeploymentConfig.MonikerConfigs.__dict__:
            if not moniker.startswith("_") and not moniker.endswith("_"):
                moniker_config = getattr(
                    self.config.DeploymentConfig.MonikerConfigs, moniker
                )
                if moniker_config.enabled:
                    for _, sprite_config in moniker_config.__dict__.items():
                        if inspect.isclass(sprite_config):
                            if sprite_config.enabled:
                                self.used_sprites.add(sprite_config.model.sprite_name)
                                for secret in sprite_config.model.SECRETS_:
                                    self.required_secrets.add(secret)

    def load_deployment_requirments(self):
        for req_var in self.config.DeploymentConfig.model.DEPLOYMENT_REQUIREMENTS_:
            self.required_deployment_vars[req_var] = getattr(
                self.config.DeploymentConfig, req_var
            )
        for secret in self.config.DeploymentConfig.model.SECRETS_:
            self.required_secrets.add(secret)

    def generate_dockerfile(self):
        dockerfile = f"""\
# Use an official Python runtime as a parent image
FROM python:3-slim-buster

# Install Git
RUN apt-get update && apt-get install -y git

# Set the working directory in the container to /shelby-as-a-service
WORKDIR /shelby-as-a-service

# Copy all files and folders from the root directory
COPY ./ ./ 

# Install python packages
RUN pip install --no-cache-dir -r app/deployments/{self.deployment_name}/requirements.txt

# Run Deployment
CMD ["python", "app/app.py", "--run_container_deployment", "{self.deployment_name}"]
        """
        with open(
            f"app/deployments/{self.deployment_name}/Dockerfile", "w", encoding="utf-8"
        ) as f:
            f.write(dockerfile)

    def generate_pip_requirements(self):
        combined_requirements = set()
        for sprite_name in self.used_sprites:
            with open(
                f"app/deployment_maker/{sprite_name}_requirements.txt",
                "r",
                encoding="utf-8",
            ) as file:
                sprite_requirements = set(file.read().splitlines())
            combined_requirements.update(sprite_requirements)

        with open(
            f"app/deployments/{self.deployment_name}/requirements.txt",
            "w",
            encoding="utf-8",
        ) as file:
            file.write("\n".join(combined_requirements))

    def generate_actions_workflow(self):
        # For github secrets
        github_secrets_string = "### Secrets ###\n"
        for secret in self.required_secrets:
            secret_name = f"{self.deployment_name.upper()}_{secret.upper()}"
            github_secrets_string += (
                f"{secret_name}:  ${{{{ secrets.{secret_name} }}}}\n"
            )
        github_secrets_string += "# Secrets in the format of 'secrets.NAME' with the 'NAME' portion added to your forked repos secrets. #"
        github_secrets_string = textwrap.indent(github_secrets_string, " " * 24)

        # For injecting into container env
        required_secrets_string = "REQUIRED_SECRETS: "
        for secret in self.required_secrets:
            required_secrets_string += f"{secret.upper()};"
        required_secrets_string = textwrap.indent(required_secrets_string, " " * 24)

        github_actions_script = textwrap.dedent(
            f"""\
        name: {self.deployment_name}-deployment

        on: workflow_dispatch

        jobs:
            docker:
                runs-on: ubuntu-latest
                env:
                    \n{github_secrets_string}
                    \n{required_secrets_string}
                      DEPLOYMENT_NAME: {self.deployment_name}

                steps:
                    - name: Checkout code
                        uses: actions/checkout@v3
                                        
                    - name: Set up Python
                        uses: actions/setup-python@v2
                        with:
                            python-version: '3.10.11'

                    - name: Cache pip dependencies
                        uses: actions/cache@v2
                        id: cache
                        with:
                            path: ~/.cache/pip 
                            key: ${{{{ runner.os }}}}-pip-${{{{  hashFiles('**app/deployments/{self.deployment_name}/requirements.txt') }}}}
                            restore-keys: |
                                ${{{{ runner.os }}}}-pip-

                    - name: Install dependencies
                        run: |
                            python -m pip install --upgrade pip
                            if [ -f app/deployments/{self.deployment_name}/requirements.txt ]; then pip install -r app/deployments/{self.deployment_name}/requirements.txt; fi

                    - name: Login to Docker registry
                        uses: docker/login-action@v2 
                        with:
                            registry: {self.required_deployment_vars['docker_registry']}
                            username: {self.required_deployment_vars['docker_username']}
                            password: ${{{{ secrets.{self.deployment_name.upper()}_DOCKER_TOKEN }}}}

                    - name: Build and push Docker image
                        uses: docker/build-push-action@v4
                        with:
                            context: .
                            file: app/deployments/{self.deployment_name}/Dockerfile
                            push: true
                            tags: {self.required_deployment_vars['docker_username']}/{self.required_deployment_vars['docker_repo']}:{self.deployment_name}-latest

                    - name: Add execute permissions to the script
                        run: chmod +x app/app.py

                    - name: Run deployment script
                        run: python app/app.py --deploy_container {self.deployment_name}
        """
        )

        github_actions_script = github_actions_script.replace("    ", "  ")
        os.makedirs(".github/workflows", exist_ok=True)
        # with open(f'.github/workflows/{deployment_settings.github_action_workflow_name}.yaml', 'w') as f:
        with open(
            f".github/workflows/{self.deployment_name}_deployment.yaml",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(github_actions_script)
