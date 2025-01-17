import importlib
import json
import os
from typing import Any, Optional, Type

import yaml


class ConfigManager:
    @staticmethod
    def check_and_create_base():
        existing_app_names = ConfigManager.check_for_existing_apps()
        if "base" not in existing_app_names:
            ConfigManager.create_app("base")
            existing_app_names = ConfigManager.check_for_existing_apps()

    @staticmethod
    def check_for_existing_apps():
        existing_app_names = []
        dir_path = "app/your_apps"
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        for app in os.listdir(dir_path):
            app_path = os.path.join(dir_path, app)
            if os.path.isdir(app_path):
                if "app_config.json" in os.listdir(app_path):
                    existing_app_names.append(app)

        return existing_app_names

    @staticmethod
    def create_app(app_name):
        """Creates a new app by copying from the template folder.
        Does not overwrite existing apps.
        To start fresh delete the app and then use this function.
        """
        dir_path = f"app/your_apps/{app_name}"

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if not os.path.exists(os.path.join(dir_path, "index/inputs")):
            os.makedirs(os.path.join(dir_path, "index/inputs"))

        # Creates blank app_config.json
        app_config_path = os.path.join(dir_path, "app_config.json")
        if not os.path.exists(app_config_path):
            with open(app_config_path, "w", encoding="utf-8") as file:
                file.write("{}")
        # Creates blank context_index.json
        index_config_path = os.path.join(dir_path, "index", "context_index.json")
        if not os.path.exists(index_config_path):
            with open(index_config_path, "w", encoding="utf-8") as file:
                file.write("{}")

        ConfigManager.create_update_env_file(app_name)

    @staticmethod
    def create_update_env_file(app_name: str, secrets: Optional[dict[str, Any]] = None):
        dir_path = f"app/your_apps/{app_name}"
        dot_env_dest_path = os.path.join(dir_path, ".env")
        dot_env_source_path = "app/template/template.env"

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
    def load_webui_sprite_default_config():
        app_name = "base"
        # In the case of local app we check for a default_local_app
        app = ConfigManager.load_app("base")
        default_settings = app.get("sprites", {}).get("webui_sprite", {}).get("optional", {})
        if default_settings.get("default_app_enabled") is True:
            existing_app_names = ConfigManager.check_for_existing_apps()
            default_local_app_name = default_settings.get("default_local_app_name", None)
            if default_local_app_name is not None and default_local_app_name in existing_app_names:
                app_name = default_local_app_name
            else:
                print(f'Default app "{default_local_app_name}" not found. Loading "base" instead.')

        return app_name

    @staticmethod
    def load_app(app_name) -> dict[str, Any]:
        try:
            with open(
                f"app/your_apps/{app_name}/app_config.json",
                "r",
                encoding="utf-8",
            ) as stream:
                config_from_file = json.load(stream)
        except json.JSONDecodeError:
            config_from_file = {}

        return config_from_file

    @staticmethod
    def save_app(app_name, updated_app_dict):
        # Save the updated configuration
        with open(
            f"app/your_apps/{app_name}/app_config.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(updated_app_dict, file, ensure_ascii=False, indent=4)

    @staticmethod
    def get_extension_configs():
        list_of_extension_configs = []
        extensions_folder = "extensions"

        # Check if the provided path is a valid directory
        if not os.path.isdir(extensions_folder):
            print(f"{extensions_folder} is not a valid directory.")
            print("Creating the 'extensions' directory...")

            # Create the directory
            os.makedirs(extensions_folder)

            print("No extensions found.")
            return []

        # Iterate through all items in the directory
        for item_name in os.listdir("extensions"):
            item_path = os.path.join("extensions", item_name)

            if item_name == "template":
                continue

            # Check if the item is a directory
            if os.path.isdir(item_path):
                config_path = os.path.join(item_path, "ext_config.yaml")

                # Check if 'ext_config.yaml' exists in the directory
                if os.path.isfile(config_path):
                    # Open and load the YAML file
                    with open(config_path, "r") as file:
                        try:
                            list_of_extension_configs.append(yaml.safe_load(file))
                            # Now config_data is a Python dictionary containing the YAML data
                            # You can process the data as needed
                        except yaml.YAMLError as exc:
                            print(f"Error in configuration file: {exc}")
        return list_of_extension_configs

    @staticmethod
    def add_extensions_to_sprite(list_of_extension_configs, sprite_class):
        sprite_class_name = sprite_class.CLASS_NAME
        for extension_config in list_of_extension_configs:
            target_sprites = extension_config.get("TARGET_SPRITES", [])
            if target_sprites is None:
                continue
            if sprite_class_name not in target_sprites:
                continue

            folder_name = extension_config.get("FOLDER_NAME")
            module_filename = extension_config.get("MODULE_FILENAME")
            class_name = extension_config.get("CLASS_NAME")
            if not (folder_name and module_filename and class_name):
                print(f"Missing configuration: {folder_name}, {module_filename}, {class_name}")
                continue

            import_path = f"extensions.{folder_name}.{module_filename}"
            try:
                module = importlib.import_module(import_path)
                cls = getattr(module, class_name)
                if getattr(sprite_class, "REQUIRED_CLASSES", None) is None:
                    sprite_class.REQUIRED_CLASSES = []
                sprite_class.REQUIRED_CLASSES.append(cls)
            except ImportError as e:
                print(f"Failed to import module: {import_path}. Error: {str(e)}")
            except AttributeError as e:
                print(
                    f"Failed to find class: {class_name} in module: {import_path}. Error: {str(e)}"
                )

    @staticmethod
    def add_extension_views_to_gradio_ui(gradio_instance, list_of_extension_configs):
        for extension_config in list_of_extension_configs:
            if extension_config.get("HAS_VIEW", False) is False:
                continue

            folder_name = extension_config.get("FOLDER_NAME")
            view_filename = extension_config.get("VIEW_FILENAME")
            view_class_name = extension_config.get("VIEW_CLASS_NAME")
            class_name = extension_config.get("CLASS_NAME")
            if not (folder_name and view_filename and view_class_name and class_name):
                print(f"Missing configuration: {folder_name}, {view_filename}, {view_class_name}")
                continue

            import_path = f"extensions.{folder_name}.{view_filename}"
            try:
                module = importlib.import_module(import_path)
                cls = getattr(module, view_class_name)
                gradio_instance.REQUIRED_CLASSES.append(cls)

            except ImportError as e:
                print(f"Failed to import module: {import_path}. Error: {str(e)}")
            except AttributeError as e:
                print(
                    f"Failed to find class: {view_class_name} in module: {import_path}. Error: {str(e)}"
                )

    # rename config to config_file_dict
    @staticmethod
    def update_config_file_from_loaded_models():
        from app.app_base import AppBase

        def recurse(class_instance, config_dict):
            if hasattr(class_instance, "config"):
                config_dict[class_instance.CLASS_NAME] = class_instance.config.model_dump()
                module_config_dict = config_dict[class_instance.CLASS_NAME]

                if required_classes := getattr(class_instance, "REQUIRED_CLASSES", None):
                    for child_module in required_classes:
                        child_class_instance = getattr(class_instance, child_module.CLASS_NAME)
                        recurse(child_class_instance, module_config_dict)

        app_dict = {}
        app_dict["app"] = AppBase.app_config.model_dump()

        for sprite in AppBase.enabled_sprite_instances:
            recurse(sprite, app_dict)

        ConfigManager.save_app(AppBase.app_config.app_name, app_dict)

    @staticmethod
    def get_config(app_name: str, path: list[str]):
        config_file_dict = ConfigManager.load_app(app_name=app_name)
        for key in path:
            config_file_dict = config_file_dict.get(key, {})
            if not config_file_dict:
                raise ValueError(f"Config not found for path {path} at key {key}")
        return config_file_dict
