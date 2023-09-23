import os
import json
from dataclasses import asdict, dataclass, field, is_dataclass


class AppManager:
    def __init__(self):
        pass

    @staticmethod
    def check_for_existing_apps():
        existing_app_names = []
        for app in os.listdir("apps"):
            app_path = os.path.join("apps", app)
            if os.path.isdir(app_path):
                if "app_config.json" in os.listdir(app_path):
                    existing_app_names.append(app)

        return existing_app_names
    
    @staticmethod
    def check_for_existing_indexes(app_name):
        existing_index_names = []
        config_from_file = AppManager.load_app_file(app_name)
        
        index_instances = config_from_file\
            .get('app_instance', {})\
            .get('services', {})\
            .get('index_service', {})\
            .get('index_instances')
        

        for index in index_instances:
            existing_index = index.get('index_name', None)
            existing_index_names.append(existing_index)
                
        return existing_index_names

    @staticmethod
    def load_app_file(app_name):
        try:
            with open(
                f"apps/{app_name}/app_config.json",
                "r",
                encoding="utf-8",
            ) as stream:
                config_from_file = json.load(stream)
        except json.JSONDecodeError:
            # If the JSON file is empty or invalid, return an empty dictionary (or handle in a way you see fit)
            config_from_file = {}

        return config_from_file

    @staticmethod
    def create_app(app_name):
        """Creates a new app by copying from the template folder.
        Does not overwrite existing apps.
        To start fresh delete the app and then use this function.
        """
        dir_path = f"apps/{app_name}"

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if not os.path.exists(os.path.join(dir_path, "index/inputs")):
            os.makedirs(os.path.join(dir_path, "index/inputs"))

        # Creates blank app_config.json
        app_config_dest_path = os.path.join(dir_path, "app_config.json")
        if not os.path.exists(app_config_dest_path):
            with open(app_config_dest_path, "w", encoding="utf-8") as file:
                file.write("{}")

        AppManager.create_update_env_file(app_name)

    @staticmethod
    def update_app_json_from_file(app_instance, app_name, update_class_instance=None):
        """Populates app_config.py from models.
        If the existing app_config.py has existing values it does not overwrite them.
        """

        app_config_file = AppManager.load_app_file(app_name)

        if app_config_file is None:
            app_config_file = {}

        # App
        if "app_instance" not in app_config_file:
            app_instance_config = {}
        else:
            app_instance_config = app_config_file["app_instance"]

        app_instance_config = AppManager.load_file_variables_as_dicts(
            app_instance, app_instance_config, update_class_instance
        )

            
        app_instance_config = AppManager._load_services(
            app_instance_config, app_instance.required_services_, update_class_instance
        )

        app_config_file["app_instance"] = app_instance_config

        # Save the updated configuration
        with open(
            f"apps/{app_name}/app_config.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(app_config_file, file, ensure_ascii=False, indent=4)

    @staticmethod
    def _load_services(config, required_services, update_class_instance):
        # App instance services
        if "services" not in config:
            config["services"] = {}
            services_config = {}
        else:
            services_config = config["services"]
            
        for required_service in required_services:
            service_model = required_service.model_
            service_class_name = service_model.service_name_

            if service_class_name not in services_config:
                services_config[service_class_name] = {}
                specific_service_config = {}
            else:
                specific_service_config = services_config[service_class_name]
            
            # Special rules for the index
            if service_class_name == "index_service":
                specific_service_config = AppManager.load_index_model_as_dicts(
                    service_model, specific_service_config
                )
            else:
                specific_service_config = AppManager.load_file_variables_as_dicts(
                    service_model, specific_service_config, update_class_instance
                )

            if hasattr(required_service, 'required_services_') and getattr(required_service, 'required_services_'):
                specific_service_config = AppManager._load_services(
                    specific_service_config,
                    required_service.required_services_,
                    update_class_instance,
                )

            services_config[service_class_name] = specific_service_config
            
        config['services'] = services_config

        return config

    @staticmethod
    def load_file_variables_as_dicts(model_class, config, update_class_instance=None):
        """Loads variables and values from models and existing app_config.py.
        Adds variables from models if they don't exist in app_config.py.
        If values exist for variables in app_config.py it uses those.
        """
        if not config:
            config = {}
        if update_class_instance is not None:
            update_class_instance_name = update_class_instance.service_name_
        else:
            update_class_instance_name = None

        if update_class_instance_name == model_class.service_name_:
            for var, val in vars(update_class_instance).items():
                if AppManager.check_for_ignored_objects(
                    var
                ) and AppManager.check_for_ignored_objects(val):
                    if val not in [None, ""]:
                        config[var] = val
                    else:
                        continue
        else:
            for var, val in vars(model_class).items():
                if AppManager.check_for_ignored_objects(
                    var
                ) and AppManager.check_for_ignored_objects(val):
                    if config.get(var) in [None, ""]:
                        config[var] = val
                    else:
                        continue

        return config

    @staticmethod
    def load_index_model_as_dicts(index_model, config):
            
        def merge_attributes(obj, config):
            if not config:
                config = {}
            
            # If obj is a list of dataclass instances
            if isinstance(obj, list) and obj and is_dataclass(obj[0]):
                obj = obj[0]
            
            # Process each attribute of the dataclass instance
            for key, val in vars(obj).items():
                config_value = config.get(key)

                # If val is a list of dataclass instances
                if isinstance(val, list) and val and is_dataclass(val[0]):
                    item_configs = config_value if isinstance(config_value, list) else [{}]
                    config[key] = [merge_attributes(val_item, item_config) for val_item, item_config in zip(val, item_configs)]
                    
                elif AppManager.check_for_ignored_objects(key):
                    config[key] = config_value if config_value is not None else val

            return config
        
        config = config or {}
        index_instances = config.get('index_instances', [])

        merged_index_instances = [
            merge_attributes(index_model.index_instances, instance)
            for instance in index_instances or [{}]
        ]

        config['index_instances'] = merged_index_instances
                                    
        
        return config

    @staticmethod
    def create_update_env_file(app_name, secrets=None):
        dir_path = f"apps/{app_name}"
        dot_env_dest_path = os.path.join(dir_path, ".env")
        dot_env_source_path = (
            "shelby_as_a_service/models/deployments/template/template.env"
        )

        # Helper function to read env file into a dictionary
        def read_env_to_dict(filepath):
            with open(filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
            return {
                line.split("=")[0].strip(): line.split("=")[1].strip()
                for line in lines
                if "=" in line
            }

        # If .env file doesn't exist, create it from template
        if not os.path.exists(dot_env_dest_path):
            with open(dot_env_source_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
                modified_lines = []
                for line in lines:
                    if line.startswith("#") or line.strip() == "":
                        continue
                    else:
                        modified_lines.append(f"{app_name.upper()}_{line.upper()}")

            with open(dot_env_dest_path, "w", encoding="utf-8") as file:
                file.writelines(modified_lines)

        # Read the existing .env and template files into dictionaries
        existing_env_dict = read_env_to_dict(dot_env_dest_path)
        template_env_dict = read_env_to_dict(dot_env_source_path)

        # Update the existing dictionary with missing keys from template
        for key, value in template_env_dict.items():
            prefixed_key = f"{app_name.upper()}_{key.upper()}"
            if prefixed_key not in existing_env_dict:
                existing_env_dict[prefixed_key] = value

        if secrets is None:
            return

        for key, value in secrets.items():
            prefixed_key = f"{app_name.upper()}_{key.upper()}"
            if prefixed_key in existing_env_dict and (value not in [None, ""]):
                existing_env_dict[prefixed_key] = secrets[key]

        # Write the updated dictionary back to the .env file
        with open(dot_env_dest_path, "w", encoding="utf-8") as file:
            for key, value in existing_env_dict.items():
                file.write(f"{key}={value}\n")

    @staticmethod
    def check_for_ignored_objects(variable):
        def has_parent_class_named(obj, class_name):
            for cls in obj.__class__.__mro__:
                if cls.__name__ == class_name:
                    return True
            return False

        # Check for string-specific conditions
        if isinstance(variable, str):
            if variable.startswith("_") or variable.endswith("_"):
                return False
            if variable in ["app_name", "secrets"]:
                return False

        # Check other conditions
        if callable(variable):
            return False
        if is_dataclass(variable):
            return False
        if isinstance(variable, type):
            return False
        if variable.__class__.__name__ == "Logger":
            return False
        if has_parent_class_named(variable, "AppBase"):
            return False

        return True
