import json
import os


class AppManager:
    @staticmethod
    def initialize_app_config(app):
        app_name = app.app_name

        existing_app_names = AppManager.check_for_existing_apps()

        if app.app_name not in existing_app_names:
            if "base" == app.app_name:
                AppManager.create_app("base")
                existing_app_names = AppManager.check_for_existing_apps()
            else:
                # Need to return here with error
                print(f"app {app.app_name} not found.")

        if "base" == app.app_name:
            app.config_manager.update_app_json_from_file(app, "base")
            # In the case of local app we check for a default_local_app
            app_config = AppManager.load_app_file(app.app_name)
            default_settings = (
                app_config.get("sprites", {}).get("web_sprite", {}).get("optional", {})
            )
            if default_settings.get("default_app_enabled") is True:
                default_local_app_name = default_settings.get(
                    "default_local_app_name", None
                )
                if (
                    default_local_app_name is not None
                    and default_local_app_name in existing_app_names
                ):
                    app_name = default_local_app_name
                else:
                    print(
                        f"Default app '{default_local_app_name}' not found. Loading 'base' instead."
                    )

        if app_name != "base":
            app.config_manager.update_app_json_from_file(app, app_name)

        return app_name

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
    def check_for_existing_apps():
        existing_app_names = []
        for app in os.listdir("apps"):
            app_path = os.path.join("apps", app)
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
