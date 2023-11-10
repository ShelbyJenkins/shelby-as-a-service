import typing
from typing import Any, Optional

import gradio as gr

from shelby_as_a_service.services.service_base import ServiceBase


def abstract_service_ui_components(
    service_name: str,
    enabled_provider_name: str,
    required_classes: list,
    provider_configs_dict: dict,
    groups_rendered: bool = True,
):
    service_providers_dict: Dict[str, Any] = {}
    service_components_list: list = []
    provider_select_dd = gr.Dropdown(
        value=enabled_provider_name,
        choices=[required_class.CLASS_NAME for required_class in required_classes],
        label="Available Providers",
        container=True,
    )

    for provider_class in required_classes:
        provider_name = provider_class.CLASS_NAME
        provider_config = provider_configs_dict.get(provider_name, {})
        config_model = provider_class.ClassConfigModel(**provider_config)
        visibility = set_current_ui_provider_visible(provider_name, enabled_provider_name)
        provider_config_components = provider_class.create_provider_ui_components(
            config_model=config_model, visibility=visibility
        )
        if not groups_rendered:
            set_components_elem_id_and_classes(
                provider_config_components, provider_name, service_name
            )
        service_providers_dict[provider_name] = provider_config_components
        service_components_list.extend(provider_config_components.values())

    if groups_rendered is False:
        provider_select_dd.change(
            fn=lambda x: toggle_current_ui_provider(
                service_providers_dict=service_providers_dict,
                requested_provider=x,
            ),
            inputs=provider_select_dd,
            outputs=service_components_list,
        )

    return provider_select_dd, service_providers_dict


def toggle_current_ui_provider(
    service_providers_dict: dict[str, Any], requested_provider: str
) -> list:
    output = []
    for provider_name, provider_config_components in service_providers_dict.items():
        visibility = set_current_ui_provider_visible(provider_name, requested_provider)
        for _ in provider_config_components.values():
            output.append(gr.update(visible=visibility))
    return output


def set_current_ui_provider_visible(provider_name: str, enabled_provider_name: str):
    if provider_name == enabled_provider_name:
        return True
    else:
        return False


def set_components_elem_id_and_classes(
    provider_config_components: dict, provider_name: str, service_name: str
):
    for component_name, component in provider_config_components.items():
        component.elem_id = component_name
        component.elem_classes = [service_name, provider_name]


def list_provider_config_components(services_components):
    output = []
    for service_dict in services_components.values():
        for provider_dict in service_dict.values():
            for component in provider_dict.values():
                output.append(component)
    return output


# This updates the config model with the values from the UI
def update_config_classes(config_model, components, *values):
    ui_state = {k: v for k, v in zip(components.keys(), values)}
    current_values = config_model.model_dump()
    current_values.update(ui_state)
    for key, value in current_values.items():
        if hasattr(config_model, key):
            setattr(config_model, key, value)

    ModuleBase.update_settings_file = True


def create_settings_event_listener(config_model, components):
    components_to_monitor = []
    for _, component in components.items():
        if isinstance(component, gr.State) or isinstance(component, gr.Button):
            continue
        else:
            components_to_monitor.append(component)

    for component in components_to_monitor:
        component.change(
            fn=lambda *x: update_config_classes(config_model, components, *x),
            inputs=components_to_monitor,
        )


def get_list_of_class_ui_names(available_classes):
    list_of_CLASS_UI_NAME = []
    for module in available_classes:
        list_of_CLASS_UI_NAME.append(module.CLASS_UI_NAME)
    return list_of_CLASS_UI_NAME


def get_class_ui_name_from_str(available_classes, requested_module):
    for module in available_classes:
        if module.CLASS_NAME == requested_module:
            return module.CLASS_UI_NAME


# def _save_load_new_secrets(self, *secrets_components):
#     for i, component in enumerate(self.global_components_["secrets"]):
#         if secrets_components[i] is not None and secrets_components[i] != "":
#             self.secrets[component.elem_id] = secrets_components[i]

#     secrets_components = self._create_secrets_components()
#     output = []
#     for component in secrets_components:
#         output.append(component.update(value="", placeholder=component.placeholder))

#     ConfigManager.create_update_env_file(self.app_name, self.secrets)

#     output_message = "Secrets saved to .env file and loaded into memory."
#     self._log(output_message)

#     if len(output) == 1:
#         return output[0]
#     return output
