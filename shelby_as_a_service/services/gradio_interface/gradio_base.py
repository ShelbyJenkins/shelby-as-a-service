from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional, Type

import gradio as gr
from app.config_manager import ConfigManager
from pydantic import BaseModel
from services.service_base import ServiceBase


class GradioLogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.captured_logs = []
        log_format = "%(levelname)s: %(asctime)s %(message)s"
        date_format = "%H:%M:%S"
        formatter = logging.Formatter(log_format, date_format)

        # Set the formatter for this handler
        self.setFormatter(formatter)

    def emit(self, record):
        self.captured_logs.append(self.format(record))


class GradioBase(ServiceBase):
    log: logging.Logger
    update_settings_file: bool = False

    async def check_for_updates(self):
        while True:
            await asyncio.sleep(5)  # non-blocking sleep
            if GradioBase.update_settings_file:
                GradioBase.update_settings_file = False
                ConfigManager.update_config_file_from_loaded_models()

    @staticmethod
    def abstract_service_ui_components(
        service_name: str,
        enabled_provider_name: str,
        required_classes: list,
        provider_configs_dict: dict,
        groups_rendered: bool = True,
    ):
        service_providers_dict: dict[str, Any] = {}
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
            visibility = GradioBase.set_current_ui_provider_visible(
                provider_name, enabled_provider_name
            )
            provider_config_components = provider_class.create_provider_ui_components(
                config_model=config_model, visibility=visibility
            )
            if not groups_rendered:
                GradioBase.set_components_elem_id_and_classes(
                    provider_config_components, provider_name, service_name
                )
            service_providers_dict[provider_name] = provider_config_components
            service_components_list.extend(provider_config_components.values())

        if groups_rendered is False:
            provider_select_dd.change(
                fn=lambda x: GradioBase.toggle_current_ui_provider(
                    service_providers_dict=service_providers_dict,
                    requested_provider=x,
                ),
                inputs=provider_select_dd,
                outputs=service_components_list,
            )

        return provider_select_dd, service_providers_dict

    @staticmethod
    def toggle_current_ui_provider(
        service_providers_dict: dict[str, Any], requested_provider: str
    ) -> list:
        output = []
        for provider_name, provider_config_components in service_providers_dict.items():
            visibility = GradioBase.set_current_ui_provider_visible(
                provider_name, requested_provider
            )
            for _ in provider_config_components.values():
                output.append(gr.update(visible=visibility))
        return output

    @staticmethod
    def set_current_ui_provider_visible(provider_name: str, enabled_provider_name: str):
        if provider_name == enabled_provider_name:
            return True
        else:
            return False

    @staticmethod
    def set_components_elem_id_and_classes(
        provider_config_components: dict, provider_name: str, service_name: str
    ):
        for component_name, component in provider_config_components.items():
            component.elem_id = component_name
            component.elem_classes = [service_name, provider_name]

    @staticmethod
    def list_provider_config_components(services_components):
        output = []
        for service_dict in services_components.values():
            for provider_dict in service_dict.values():
                for component in provider_dict.values():
                    output.append(component)
        return output

    @staticmethod
    # This updates the config model with the values from the UI
    def create_settings_event_listener(config_model: BaseModel, components):
        def update_config_classes(config_model, components, *values):
            ui_state = {k: v for k, v in zip(components.keys(), values)}
            current_values = config_model.model_dump()
            current_values.update(ui_state)
            for key, value in current_values.items():
                if hasattr(config_model, key):
                    setattr(config_model, key, value)

            GradioBase.update_settings_file = True

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

    @classmethod
    def get_logs_and_send_to_interface(cls):
        handler = GradioLogCaptureHandler()
        cls.log.addHandler(handler)
        new_logs = []
        try:
            while True:
                while handler.captured_logs:
                    new_logs.append(handler.captured_logs.pop(0))
                    yield "\n".join(new_logs)
                    if "end_log" in new_logs:
                        return

                # Wait for a short period before checking for new logs
                time.sleep(0.1)
        finally:
            cls.log.removeHandler(handler)

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
