import typing
from typing import Any, Dict, Optional

import gradio as gr
from app.module_base import ModuleBase


def abstract_service_ui_components(
    enabled_provider_name: str,
    required_classes: list,
    provider_configs_dict: dict,
    groups_rendered: bool = True,
):
    ui_components_list: list = []
    ui_components_dict: Dict[str, Any] = {}
    provider_ui_views: list = []

    provider_select_dropdown = gr.Dropdown(
        value=enabled_provider_name,
        choices=[required_class.CLASS_NAME for required_class in required_classes],
        label="Available Providers",
        container=True,
    )

    ui_components_dict["provider_select_dropdown"] = provider_select_dropdown
    ui_components_list.append(provider_select_dropdown)

    for provider_class in required_classes:
        provider_name = provider_class.CLASS_NAME
        provider_config = provider_configs_dict.get(provider_name, {})
        provider_instance = provider_class(config_file_dict=provider_config)
        if groups_rendered:
            ui_components_dict[provider_name] = provider_instance.create_provider_ui_components()
        else:
            visibility = set_current_ui_provider(provider_name, enabled_provider_name)
            with gr.Group(visible=visibility) as provider_view:
                ui_components_dict[
                    provider_name
                ] = provider_instance.create_provider_ui_components()
            provider_ui_views.append(provider_view)

        ui_components_list.extend(ui_components_dict[provider_name].values())

    if groups_rendered is False:

        def toggle_current_ui_provider(list_of_class_names: list[str], requested_model: str):
            output = []
            for provider_name in list_of_class_names:
                visibility = set_current_ui_provider(provider_name, requested_model)
                output.append(gr.Group(visible=visibility))
            return output

        provider_select_dropdown.change(
            fn=lambda x: toggle_current_ui_provider(
                list_of_class_names=[
                    required_class.CLASS_NAME for required_class in required_classes
                ],
                requested_model=x,
            ),
            inputs=provider_select_dropdown,
            outputs=provider_ui_views,
        )

    return ui_components_list, ui_components_dict


def set_current_ui_provider(provider_name: str, enabled_provider_name: str):
    if provider_name == enabled_provider_name:
        return True
    else:
        return False


# This updates the config model with the values from the UI
# Need a second class for updates to sqlite
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
