import os
import json
from dataclasses import is_dataclass
from dotenv import load_dotenv


app_config_path: str = "app_instance"
index_config_path: str = "index"
sprite_config_path: str = "services"  # Change to sprites
agent_config_path: str = "services"  # Change to agents
service_config_path: str = "services"  # Change to services
provider_config_path: str = "services"  # Change to providers


def setup_service_config(instance):
    config_path = get_config_path(instance)
    config = get_config(instance, config_path)
    set_config(instance, config)
    set_secrets(instance)


def get_config_path(instance):
    """Builds path to the service settings in the config file"""

    base_path = [app_config_path]

    if instance.__class__.__name__ == "IndexModel":
        base_path.append(index_config_path)
        return base_path

    base_path.append(sprite_config_path)
    if sprite_name := getattr(instance, "sprite_name", None):
        base_path.append(sprite_name)
        return base_path

    base_path.extend([instance.parent_sprite.sprite_name, agent_config_path])
    if agent_name := getattr(instance, "agent_name", None):
        base_path.append(agent_name)
        return base_path

    base_path.extend([instance.parent_agent.agent_name, service_config_path])
    if service_name := getattr(instance, "service_name", None):
        base_path.append(service_name)
        return base_path

    base_path.extend([instance.parent_service.service_name, provider_config_path])
    if provider_name := getattr(instance, "provider_name", None):
        base_path.append(provider_name)
        return base_path

    return None


def get_config(instance, config_path):
    # Create a copy of the base config, and path to the config
    config = instance.app.config.copy()
    for path in config_path:
        config = config.get(path, None)
        if config is None:
            config = None
            break

    return config


def set_config(instance, config):
    # from_file overwrites class vars from file
    config = {**vars(instance), **(config or {})}

    # Removes services object used to structure the json file
    if config.get("services", None):
        config.pop("services")

    for key, value in config.copy().items():
        if check_for_ignored_objects(key) and check_for_ignored_objects(value):
            setattr(instance, key, value)
        else:
            config.pop(key)

    instance.config = config


def set_secrets(instance):
    if hasattr(instance, "required_secrets") and instance.required_secrets:
        for secret in instance.required_secrets:
            secret_str = f"{instance.app.app_name}_{secret}".upper()
            env_secret = os.environ.get(secret_str)

            instance.app.secrets[secret] = env_secret
            instance.app.required_secrets.append(secret)


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

    app_instance_config = load_file_variables_as_dicts(
        app_instance, app_instance_config, update_class_instance
    )

    app_instance_config = _load_services(
        app_name,
        app_instance_config,
        app_instance.required_services_,
        update_class_instance,
    )

    app_config_file["app_instance"] = app_instance_config

    # Save the updated configuration
    with open(
        f"apps/{app_name}/app_config.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(app_config_file, file, ensure_ascii=False, indent=4)


def _load_services(app_name, config, required_services, update_class_instance):
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
            specific_service_config = load_file_variables_as_dicts(
                service_model, specific_service_config, update_class_instance
            )
            if specific_service_config.get("index_name", None) is None:
                specific_service_config["index_name"] = f"{app_name}_index"

            specific_service_config = load_data_domains_as_dicts(
                app_name,
                required_service,
                specific_service_config,
                update_class_instance,
            )

        else:
            specific_service_config = load_file_variables_as_dicts(
                service_model, specific_service_config, update_class_instance
            )

        if hasattr(required_service, "required_services_") and getattr(
            required_service, "required_services_"
        ):
            specific_service_config = _load_services(
                app_name,
                specific_service_config,
                required_service.required_services_,
                update_class_instance,
            )

        services_config[service_class_name] = specific_service_config

    config["services"] = services_config

    return config


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
            if check_for_ignored_objects(var) and check_for_ignored_objects(val):
                if val not in [None, ""]:
                    config[var] = val
                else:
                    continue
    else:
        for var, val in vars(model_class).items():
            if check_for_ignored_objects(var) and check_for_ignored_objects(val):
                if config.get(var) in [None, ""]:
                    config[var] = val
                else:
                    continue

    return config


def load_data_domains_as_dicts(
    app_name, index_service, index_config, update_class_instance=None
):
    data_domain_service = index_service.data_domain_service_
    data_domain_model = data_domain_service.model_

    index_data_domains_config = index_config.get("index_data_domains", [])
    index_data_domains = []
    for data_domain_config in index_data_domains_config or [{}]:
        data_domain_config = _load_services(
            app_name,
            data_domain_config,
            data_domain_service.required_services_,
            update_class_instance,
        )
        data_domain_config = load_file_variables_as_dicts(
            data_domain_model, data_domain_config, update_class_instance
        )

        data_domain_config = load_data_sources_as_dicts(
            app_name,
            data_domain_service,
            data_domain_config,
            update_class_instance=None,
        )

        index_data_domains.append(data_domain_config)

    index_config["index_data_domains"] = index_data_domains

    return index_config


def load_data_sources_as_dicts(
    app_name, data_domain_service, data_domain_config, update_class_instance=None
):
    data_source_service = data_domain_service.data_source_service_
    data_source_model = data_source_service.model_

    data_sources_config = data_domain_config.get("data_domain_sources", [])
    data_sources = []
    for data_source_config in data_sources_config or [{}]:
        data_source_config = _load_services(
            app_name,
            data_source_config,
            data_source_service.required_services_,
            update_class_instance,
        )
        data_source_config = load_file_variables_as_dicts(
            data_source_model, data_source_config, update_class_instance
        )
        data_sources.append(data_source_config)

    data_domain_config["data_domain_sources"] = data_sources

    return data_domain_config


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
        if variable in ["app_name", "secrets", "app"]:
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
