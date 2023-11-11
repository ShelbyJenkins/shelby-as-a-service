import asyncio
import threading
import typing
from decimal import Decimal
from typing import Any, Optional, Type

import gradio as gr
from app.config_manager import ConfigManager
from pydantic import BaseModel
from services.gradio_interface import AVAILABLE_VIEW_NAMES, AVAILABLE_VIEWS
from services.gradio_interface.gradio_themes import AtYourServiceTheme
from services.service_base import ServiceBase


class GradioService(ServiceBase):
    CLASS_NAME: str = "gradio_ui"
    CLASS_UI_NAME: str = "gradio_ui"
    AVAILABLE_VIEWS: list[Type] = AVAILABLE_VIEWS
    AVAILABLE_VIEW_NAMES = AVAILABLE_VIEW_NAMES
    SETTINGS_UI_COL = 2
    PRIMARY_UI_COL = 8

    class ClassConfigModel(BaseModel):
        current_ui_view_name: str = "Chat"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_view_instances: list = []

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        ConfigManager.add_extension_views_to_gradio_ui(self, self.list_of_extension_configs)
        super().__init__(config=config, **kwargs)
        class_config = config.get(self.CLASS_NAME, {})
        for view in self.AVAILABLE_VIEWS:
            self.list_of_view_instances.append(view(class_config.get(view.CLASS_NAME, {})))

    def create_gradio_interface(self):
        all_setting_ui_tabs = []
        all_primary_ui_rows = []

        with gr.Blocks(
            theme=AtYourServiceTheme(),
            css=AtYourServiceTheme.css,
        ) as webui_client:
            with gr.Row(elem_id="main_row"):
                with gr.Column(
                    elem_id="settings_ui_col", scale=self.SETTINGS_UI_COL
                ) as settings_ui_col:
                    with gr.Tabs(selected=self.config.current_ui_view_name):
                        for view_class in self.AVAILABLE_VIEWS:
                            all_setting_ui_tabs.append(self.settings_ui_creator(view_class))

                with gr.Column(
                    elem_id="primary_ui_col", scale=self.PRIMARY_UI_COL
                ) as primary_ui_col:
                    for view_class in self.AVAILABLE_VIEWS:
                        all_primary_ui_rows.append(self.primary_ui_creator(view_class))

            self.create_nav_events(
                all_setting_ui_tabs, all_primary_ui_rows, settings_ui_col, primary_ui_col
            )

            webui_client.load(
                fn=lambda: self.set_agent_view(requested_view=self.config.current_ui_view_name),
                outputs=all_primary_ui_rows + [settings_ui_col, primary_ui_col],
            )

            threading.Thread(target=asyncio.run, args=(self.check_for_updates(),)).start()

            webui_client.queue()
            # webui_client.launch(prevent_thread_lock=True, show_error=True)
            try:
                webui_client.launch(show_error=True)
            except Warning as w:
                self.log.warning(w)
                gr.Warning(message=str(w))

    @staticmethod
    def primary_ui_creator(view):
        view_name = view.CLASS_NAME

        with gr.Row(
            elem_classes="primary_ui_row",
            elem_id=f"{view_name}_primary_ui_row",
            visible=False,
        ) as primary_ui_row:
            view.create_primary_ui()

        return primary_ui_row

    @staticmethod
    def settings_ui_creator(view):
        agent_name = view.CLASS_NAME
        agent_ui_name = view.CLASS_UI_NAME

        with gr.Tab(
            id=agent_ui_name,
            label=agent_ui_name,
            elem_id=f"{agent_name}_settings_ui_tab",
        ) as agent_nav_tab:
            view.create_settings_ui()

        return agent_nav_tab

    def create_nav_events(
        self, all_setting_ui_tabs, all_primary_ui_rows, settings_ui_col, primary_ui_col
    ):
        outputs = []
        outputs += all_primary_ui_rows
        outputs.append(settings_ui_col)
        outputs.append(primary_ui_col)

        for agent_nav_tab in all_setting_ui_tabs:
            agent_nav_tab.select(
                fn=self.get_nav_evt,
                inputs=None,
                outputs=outputs,
            )

    def get_nav_evt(self, evt: gr.SelectData):
        output = self.set_agent_view(evt.value)
        return output

    def set_agent_view(self, requested_view: str):
        output = []
        settings_ui_scale = 1
        primary_ui_scale = 1

        for view_instance in self.list_of_view_instances:
            if requested_view == view_instance.CLASS_UI_NAME:
                output.append(gr.Row(visible=True))
                self.config.current_ui_view_name = view_instance.CLASS_UI_NAME
                settings_ui_scale = view_instance.SETTINGS_UI_COL
                primary_ui_scale = view_instance.PRIMARY_UI_COL
            else:
                output.append(gr.Row(visible=False))

        output.append(gr.Column(scale=settings_ui_scale))
        output.append(gr.Column(scale=primary_ui_scale))
        self.update_settings_file = True
        return output

    async def check_for_updates(self):
        while True:
            await asyncio.sleep(5)  # non-blocking sleep
            if self.update_settings_file:
                self.update_settings_file = False
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
            visibility = GradioService.set_current_ui_provider_visible(
                provider_name, enabled_provider_name
            )
            provider_config_components = provider_class.create_provider_ui_components(
                config_model=config_model, visibility=visibility
            )
            if not groups_rendered:
                GradioService.set_components_elem_id_and_classes(
                    provider_config_components, provider_name, service_name
                )
            service_providers_dict[provider_name] = provider_config_components
            service_components_list.extend(provider_config_components.values())

        if groups_rendered is False:
            provider_select_dd.change(
                fn=lambda x: GradioService.toggle_current_ui_provider(
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
            visibility = GradioService.set_current_ui_provider_visible(
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

    @classmethod
    # This updates the config model with the values from the UI
    def create_settings_event_listener(cls, config_model, components):
        def update_config_classes(config_model, components, *values):
            ui_state = {k: v for k, v in zip(components.keys(), values)}
            current_values = config_model.model_dump()
            current_values.update(ui_state)
            for key, value in current_values.items():
                if hasattr(config_model, key):
                    setattr(config_model, key, value)

            cls.update_settings_file = True

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
