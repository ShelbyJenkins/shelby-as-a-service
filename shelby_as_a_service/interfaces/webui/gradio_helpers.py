import typing
from typing import Any, Dict, Optional

import gradio as gr
from app.module_base import ModuleBase


def toggle_current_ui_provider(list_of_class_names: list[str], requested_model: str):
    output = []
    for provider_name in list_of_class_names:
        if requested_model == provider_name:
            output.append(gr.Group(visible=True))
        else:
            output.append(gr.Group(visible=False))
    return output


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
