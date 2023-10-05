from typing import Any, Dict, List, Optional

import gradio as gr


def list_available(class_model) -> Optional[List[Any]]:
    if available_providers := getattr(class_model, "AVAILABLE_PROVIDERS", None):
        return [provider.PROVIDER_NAME for provider in available_providers]
    if available_models := getattr(class_model, "AVAILABLE_MODELS", None):
        return [modes.MODEL_NAME for modes in available_models]
    if available_agents := getattr(class_model, "AVAILABLE_AGENTS", None):
        return [agent.AGENT_UI_NAME for agent in available_agents]
    return None


def dropdown_default_value(class_model):
    choices = list_available(class_model)
    if choices:
        return choices[0]
    return None


def dropdown_choices(class_model):
    choices = list_available(class_model)
    if choices:
        return choices
    return None


def check_for_web_data(web_data_added):
    if web_data_added:
        return True
    raise gr.Error("No valid web data found!")


def comp_values_to_dict(ui, *values) -> Dict[str, Any]:
    group_name = values[0]
    comps_keys = ui[group_name]["comps"].keys()
    return {k: v for k, v in zip(comps_keys, values)}


# # Interface functions
# def _save_config_to_memory(self, *settings_components):
#     """Updates settings in memory using input from the gradio settings_components.
#     Takes  input from config_blocks, and sets the class using elem_classes field.
#     Then uses the label field to set the attr with the value from the input.
#     """
#     class_components = self.global_components_["settings_components"][
#         settings_components[0]
#     ]

#     if settings_components[0] == "web_sprite
# ":
#         class_instance = self
#     else:
#         class_instance = getattr(self, settings_components[0])

#     for i, component in enumerate(settings_components):
#         if i == 0:
#             continue
#         setattr(class_instance, class_components[i].elem_id, component)

#     output_message = "Config settings saved to memory."
#     self._log(output_message)

#     return output_message

# def _save_config_to_file(self, *settings_components):
#     self._save_config_to_memory(*settings_components)

#     if settings_components[0] == "web_sprite
# ":
#         class_instance = self
#     else:
#         class_instance = getattr(self, settings_components[0])

#     AppManager.update_app_json_from_file(
#         self.app, self.app.app_name, class_instance
#     )
#     output_message = "Config settings saved to file."

#     self._log(output_message)

#     return output_message

# def _save_load_new_secrets(self, *secrets_components):
#     for i, component in enumerate(self.global_components_["secrets"]):
#         if secrets_components[i] is not None and secrets_components[i] != "":
#             self.secrets[component.elem_id] = secrets_components[i]

#     secrets_components = self._create_secrets_components()
#     output = []
#     for component in secrets_components:
#         output.append(component.update(value="", placeholder=component.placeholder))

#     AppManager.create_update_env_file(self.app.app_name, self.secrets)

#     output_message = "Secrets saved to .env file and loaded into memory."
#     self._log(output_message)

#     if len(output) == 1:
#         return output[0]
#     return output

# def _update_ui_settings_components(self, *settings_components):
#     """Gradio can only send a single object (list or dict),
#     so we add the class_name to an invisible textbox.
#     This is used to identify the class to update the components."""

#     class_name = settings_components[0]
#     if class_name == "web_sprite
# ":
#         class_instance = self
#     else:
#         class_instance = getattr(self, class_name)
#     components = self.global_components_["settings_components"][class_name]

#     output = []
#     for i, component in enumerate(components):
#         if i == 0:
#             value = component.elem_id
#         else:
#             value = getattr(class_instance, component.elem_id)
#         output.append(component.update(value=value))

#     output_message = f"Settings for {class_name} loaded into UI."
#     self._log(output_message)

#     return output

# def _load_new_app_from_file(self, load_app_name=None):
#     """Loads new app to app object."""

#     self.existing_app_names_ = AppManager.check_for_existing_apps()

#     if load_app_name is not None:
#         if load_app_name not in self.existing_app_names_:
#             output_message = f"Can't find a app named: '{load_app_name}'"
#             raise gr.Error(output_message)
#         if load_app_name == self.app.app_name:
#             output_message = f"app already loaded: '{load_app_name}'"
#             raise gr.Error(output_message)
#         self.app.app_name = load_app_name

#     self.app.setup_app(self.app)

#     for attr, _ in vars(self.model_).items():
#         val = getattr(self.app.web_sprite
# , attr, None)
#         setattr(self, attr, val)

#     for service in self.required_services_:
#         service_name = service.model_.service_name_
#         service_instance = getattr(self.app.web_sprite
# , service_name)
#         setattr(self, service_name, service_instance)

#     output_message = f"app loaded: '{self.app.app_name}'"
#     self._log(output_message)

# def _create_new_app(self, new_app_name):
#     new_app_name = new_app_name.strip()

#     if len(new_app_name) < 3:
#         output_message = "Please enter a longer app name"
#         self._log(output_message)

#     elif not all(char.isalnum() or char == "_" for char in new_app_name):
#         output_message = "Please only use alpha numeric chars and '_' chars."
#         self._log(output_message)
#     else:
#         if not self.existing_app_names_:
#             self.existing_app_names_ = AppManager.check_for_existing_apps()
#         if new_app_name in self.existing_app_names_:
#             output_message = "That app already exists. Please delete it first"
#             self._log(output_message)
#         else:
#             AppManager().create_app(new_app_name)
#             AppManager().update_app_json_from_file(self.app, new_app_name)
#             self.existing_app_names_ = AppManager.check_for_existing_apps()
#             output_message = f" app '{new_app_name}' created"
#             self._log(output_message)

#     return (
#         gr.Textbox.update(value=""),
#         gr.Dropdown.update(
#             value=self.existing_app_names_[0],
#             choices=self.existing_app_names_,
#         ),
#         gr.Dropdown.update(value="Danger!", choices=self.existing_app_names_),
#     )

# def _delete_app(self, delete_app_name, delete_app_chk_box):
#     if delete_app_name == self.app_name:
#         output_message = "Can't delete in use app. Please switch first."
#         self._log(output_message)
#     elif delete_app_chk_box is False:
#         output_message = "Please check check the box to confirm delete"
#         self._log(output_message)
#     else:
#         base_dir = "apps"

#         app_path = os.path.join(base_dir, delete_app_name)
#         if os.path.exists(app_path):
#             try:
#                 shutil.rmtree(app_path)
#                 output_message = f"Successfully deleted app: '{delete_app_name}'"
#                 self._log(output_message)
#             except Exception as error:
#                 output_message = (
#                     f"Error deleting app: '{delete_app_name}'. Error: {str(error)}"
#                 )
#                 self._log(output_message)
#         else:
#             output_message = f"app: '{delete_app_name}' not found."
#             self._log(output_message)

#         self.existing_app_names_ = AppManager.check_for_existing_apps()

#     return (
#         gr.Dropdown.update(choices=self.existing_app_names_),
#         gr.Dropdown.update(value="Danger!", choices=self.existing_app_names_),
#         gr.Checkbox.update(value=False),
#     )

# # App functionality
# async def _run_ceq_request(self, request):
#     # Required to run multiple requests at a time in async
#     with ThreadPoolExecutor() as executor:
#         loop = asyncio.get_event_loop()
#         response = await loop.run_in_executor(
#             executor, self.ceq_agent.run_context_enriched_query, request
#         )
#         return "", response
