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
    def update_app_json_from_model(app_instance, app_name):
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
            app_instance, app_instance_config
        )

        # App instance services
        if "services" not in app_instance_config:
            app_instance_config["services"] = {}
            services_config = {}
        else:
            services_config = app_instance_config["services"]
                
        for app_instance_required_service in app_instance.required_services_:
            service_model = app_instance_required_service.model_
            service_class_name = service_model.service_name_

            # App instance Service
            if service_class_name not in services_config:
                service_config = {}
            else:
                service_config = services_config[service_class_name]
                
            # Special rules for the index
            if service_class_name == 'index_service':
                service_config = AppManager.load_index_model_as_dicts(
                    service_model, service_config
                )
            else:
                service_config = AppManager.load_file_variables_as_dicts(
                    service_model, service_config
                )

            app_instance_config["services"][service_class_name] = service_config

        app_config_file["app_instance"] = app_instance_config
 
 
        # Sprites
        for sprite_class in app_instance.required_sprites_:
            sprite_model = sprite_class.model_
            sprite_name_model = sprite_model.service_name_
            if sprite_name_model not in app_config_file:
                sprite_config = {}
            else:
                sprite_config = app_config_file[sprite_name_model]

            sprite_config = AppManager.load_file_variables_as_dicts(
                sprite_model, sprite_config
            )

            # Services
            if "services" not in sprite_config:
                sprite_config["services"] = {}
                services_config = {}
            else:
                services_config = sprite_config["services"]

            for sprite_class_required_service in sprite_class.required_services_:
                service_model = sprite_class_required_service.model_
                service_class_name = service_model.service_name_

                # Service
                if service_class_name not in services_config:
                    service_config = {}
                else:
                    service_config = services_config[service_class_name]

                service_config = AppManager.load_file_variables_as_dicts(
                    service_model, service_config
                )

                sprite_config["services"][service_class_name] = service_config

            app_config_file[sprite_name_model] = sprite_config

        # Save the updated configuration
        with open(
            f"apps/{app_name}/app_config.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(app_config_file, file, ensure_ascii=False, indent=4)

    @staticmethod
    def load_file_variables_as_dicts(model_class, config):
        """Loads variables and values from models and existing app_config.py.
        Adds variables from models if they don't exist in app_config.py.
        If values exist for variables in app_config.py it uses those.
        """
        if not config:
            config = {}
        # Handle 'required'
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
    def load_index_model_as_dicts(index_model, config: dict):
        
        def merge_attributes(obj, config: dict):
            for key, default_value in vars(obj).items():
                config_value = config.get(key) if config else None  # Important check
                if config_value is None:
                    continue  # We skip this attribute since the config doesn't have data for it
                if is_dataclass(default_value):
                    setattr(obj, key, merge_attributes(default_value, config_value))
                elif isinstance(default_value, list) and len(default_value) > 0 and is_dataclass(default_value[0]):
                    setattr(obj, key, [merge_attributes(default_value[0], item_config) for item_config in config_value])
                else:
                    setattr(obj, key, config_value)
            return obj

        return asdict(merge_attributes(index_model, config))

    @staticmethod
    def update_app_json_from_memory(app_instance, app_name):
        """Populates app_config.py from models.
        If the existing app_config.py has existing values it does not overwrite them.
        """

        app_config_file = AppManager.load_app_file(app_name)

        if app_config_file is None:
            app_config_file = {}

        # app
        if "app_instance" not in app_config_file:
            app_instance_config = {}
        else:
            app_instance_config = app_config_file["app_instance"]

        app_config_file[
            "app_instance"
        ] = AppManager.load_memory_variables_as_dicts(
            app_instance.model_, app_instance_config
        )

        # Sprite
        for sprite_class in app_instance.required_sprites_:
            sprite_model = sprite_class.model_
            sprite_name_model = sprite_model.service_name_
            sprite_instance = getattr(app_instance, sprite_name_model)
            if sprite_name_model not in app_config_file:
                sprite_config = {}
            else:
                sprite_config = app_config_file[sprite_name_model]

            sprite_config = AppManager.load_memory_variables_as_dicts(
                sprite_instance, sprite_config
            )

            # Services
            if "services" not in sprite_config:
                sprite_config["services"] = {}
                services_config = {}
            else:
                services_config = sprite_config["services"]

            # Service
            for sprite_class_required_service in sprite_class.required_services_:
                service_model = sprite_class_required_service.model_
                service_class_name = service_model.service_name_
                service_instance = getattr(sprite_instance, service_class_name)
                if service_class_name not in services_config:
                    service_config = {}
                else:
                    service_config = services_config[service_class_name]

                service_config = AppManager.load_memory_variables_as_dicts(
                    service_instance, service_config
                )

                sprite_config["services"][service_class_name] = service_config

            app_config_file[sprite_name_model] = sprite_config

        # Save the updated configuration
        with open(
            f"apps/{app_name}/app_config.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(app_config_file, file, ensure_ascii=False, indent=4)

    @staticmethod
    def load_memory_variables_as_dicts(class_instance, config):
        """Loads variables and values from class_instance and existing app_config.py.
        If values exist for variables in class_instance it uses those.
        """
        if not config:
            config = {}

        for var, value in sorted(vars(class_instance).items()):  # sort by variable name
            if var in config:
                if value not in [None, ""]:
                    config[var] = value
                else:
                    continue

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
                        modified_lines.append(
                            f"{app_name.upper()}_{line.upper()}"
                        )

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
