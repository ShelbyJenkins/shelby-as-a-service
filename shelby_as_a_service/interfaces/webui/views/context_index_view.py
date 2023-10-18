from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from agents.ingest.ingest_agent import IngestAgent
from app_config.context_index.index_base import ContextIndexService, DataDomain, DataSource
from app_config.module_base import ModuleBase
from pydantic import BaseModel
from services.database.database_service import DatabaseService


class ContextIndexView(ModuleBase):
    MODULE_NAME: str = "context_index_view"
    MODULE_UI_NAME: str = "Context Index"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6
    REQUIRED_MODULES: list[Type] = [IngestAgent, DatabaseService]

    class ModuleConfigModel(BaseModel):
        current_data_domain_name: str = "default_data_domain"
        current_data_source_name: str = "default_data_source"

        class Config:
            extra = "ignore"

    config: ModuleConfigModel
    list_of_module_ui_names: list
    list_of_module_instances: list
    ingest_agent: IngestAgent
    database_service: DatabaseService

    context_index_service: ContextIndexService
    the_context_index: ContextIndexService.TheContextIndex
    current_data_domain_instance: Any = None

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

        self.components = {}

    def create_primary_ui(self):
        with gr.Column(elem_classes="primary_ui_col"):
            self.components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {ContextIndexView.MODULE_UI_NAME}",
                elem_id="chat_tab_out_text",
                elem_classes="chat_tab_out_text_class",
                scale=7,
            )

        # self.create_event_handlers()

    def create_settings_ui(self):
        with gr.Column():
            # self.quick_add()
            # self.add_source()
            self.add_data_domain()
            with gr.Tab(label="Index Management"):
                pass

    def quick_add(self):
        with gr.Tab("Quick Add"):
            self.components["ingest_button"] = gr.Button(
                value="Ingest",
                variant="primary",
                elem_classes="chat_tab_button",
                min_width=0,
            )
            self.components["url_textbox"] = gr.Textbox(
                placeholder="Paste URL Link",
                lines=1,
                show_label=False,
            )
            self.components["file_path_textbox"] = gr.Textbox(
                placeholder="Paste Filepath (or drag and drop)",
                lines=1,
                visible=False,
                show_label=False,
            )

            with gr.Row():
                with gr.Column(min_width=0):
                    self.components["url_or_file_radio"] = gr.Radio(
                        value="From Website",
                        choices=["From Website", "From Local File"],
                        interactive=True,
                        show_label=False,
                        min_width=0,
                    )
                with gr.Column(min_width=0, scale=3):
                    with gr.Row():
                        self.components["default_web_data_source_drp"] = gr.Dropdown(
                            visible=True,
                            allow_custom_value=True,
                            value=self.the_context_index.index_data_domains[0].data_domain_sources[0].data_source_name,
                            choices=[
                                cls.data_source_name
                                for cls in self.the_context_index.index_data_domains[0].data_domain_sources
                            ],
                            show_label=False,
                            interactive=True,
                        )
                        self.components["default_local_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.the_context_index.index_data_domains[0].data_domain_sources[0].data_source_name,
                            choices=[
                                cls.data_source_name
                                for cls in self.the_context_index.index_data_domains[0].data_domain_sources
                            ],
                            show_label=False,
                            interactive=True,
                        )
                    with gr.Row():
                        self.components["custom_web_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.the_context_index.index_data_domains[0].data_domain_sources[0].data_source_name,
                            choices=[
                                cls.data_source_name
                                for cls in self.the_context_index.index_data_domains[0].data_domain_sources
                            ],
                            show_label=False,
                            interactive=True,
                        )
                        self.components["custom_local_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.the_context_index.index_data_domains[0].data_domain_sources[0].data_source_name,
                            choices=[
                                cls.data_source_name
                                for cls in self.the_context_index.index_data_domains[0].data_domain_sources
                            ],
                            show_label=False,
                            interactive=True,
                        )
                    self.components["default_custom_checkbox"] = gr.Checkbox(label="Use custom")

            self.components["files_drop_box"] = gr.File(
                visible=False,
                label="Drag and drop file",
            )

            def toggle_web_or_local(value):
                if value == "From Website":
                    return [
                        gr.Textbox(visible=True),
                        gr.File(visible=False),
                        gr.Textbox(visible=False),
                    ]
                return [
                    gr.Textbox(visible=False),
                    gr.File(visible=True),
                    gr.Textbox(visible=True),
                ]

            def toggle_default_custom(url_or_file_radio, default_custom_checkbox):
                if url_or_file_radio == "From Website":
                    if default_custom_checkbox == False:
                        return [
                            gr.Dropdown(visible=True),
                            gr.Dropdown(visible=False),
                            gr.Dropdown(visible=False),
                            gr.Dropdown(visible=False),
                        ]
                    return [
                        gr.Dropdown(visible=False),
                        gr.Dropdown(visible=False),
                        gr.Dropdown(visible=True),
                        gr.Dropdown(visible=False),
                    ]
                else:
                    if default_custom_checkbox == False:
                        return [
                            gr.Dropdown(visible=False),
                            gr.Dropdown(visible=True),
                            gr.Dropdown(visible=False),
                            gr.Dropdown(visible=False),
                        ]
                    return [
                        gr.Dropdown(visible=False),
                        gr.Dropdown(visible=False),
                        gr.Dropdown(visible=False),
                        gr.Dropdown(visible=True),
                    ]

            self.components["default_custom_checkbox"].change(
                fn=toggle_default_custom,
                inputs=[
                    self.components["url_or_file_radio"],
                    self.components["default_custom_checkbox"],
                ],
                outputs=[
                    self.components["default_web_data_source_drp"],
                    self.components["default_local_data_source_drp"],
                    self.components["custom_web_data_source_drp"],
                    self.components["custom_local_data_source_drp"],
                ],
            )

            self.components["url_or_file_radio"].change(
                fn=toggle_default_custom,
                inputs=[
                    self.components["url_or_file_radio"],
                    self.components["default_custom_checkbox"],
                ],
                outputs=[
                    self.components["default_web_data_source_drp"],
                    self.components["default_local_data_source_drp"],
                    self.components["custom_web_data_source_drp"],
                    self.components["custom_local_data_source_drp"],
                ],
            ).then(
                fn=toggle_web_or_local,
                inputs=self.components["url_or_file_radio"],
                outputs=[
                    self.components["url_textbox"],
                    self.components["file_path_textbox"],
                    self.components["files_drop_box"],
                ],
            )

    def add_source(self):
        with gr.Tab(label="Add Source"):
            with gr.Row():
                self.components["url_or_file_radio"] = gr.Radio(
                    value="From Website",
                    choices=["From Website", "From Local File"],
                    interactive=True,
                    show_label=False,
                    min_width=0,
                )
                self.components["source_preset"] = gr.Dropdown(
                    value="Github",
                    choices=["Github", "Save to Topic Domain", "Don't Save"],
                    info="Applies presets that improves performance.",
                    interactive=True,
                    show_label=False,
                    min_width=0,
                )
                self.components["ingest_button"] = gr.Button(
                    value="Ingest",
                    variant="primary",
                    elem_classes="chat_tab_button",
                    min_width=0,
                )

            self.components["url_textbox"] = gr.Textbox(
                placeholder="Paste URL Link",
                lines=1,
                show_label=False,
            )
            self.components["files_drop_box"] = gr.File(
                visible=False,
                label="Drag and drop file",
            )
            self.components["file_path_textbox"] = gr.Textbox(
                placeholder="or Paste Filepath",
                lines=1,
                visible=False,
                show_label=False,
            )
            with gr.Tab("Save Document"):
                gr.Checkbox(label="test")
            with gr.Tab(open=False, label="Custom Loader"):
                with gr.Row():
                    self.components["custom_loader"] = gr.Dropdown(
                        value="Github",
                        choices=["Github", "Save to Topic Domain", "Don't Save"],
                        label="Source",
                        interactive=True,
                    )
                    self.components["test_loader_button"] = gr.Button(
                        value="Test Loader",
                        variant="primary",
                        elem_classes="chat_tab_button",
                        min_width=0,
                    )

                # Settings go here
                gr.Checkbox(label="test")
            with gr.Tab(open=False, label="Custom Text Processor"):
                with gr.Row():
                    self.components["custom_text_proc"] = gr.Dropdown(
                        value="Github",
                        choices=["Github", "Save to Topic Domain", "Don't Save"],
                        label="Source",
                        interactive=True,
                    )
                    self.components["test_proc"] = gr.Button(
                        value="Test Loader",
                        variant="primary",
                        elem_classes="chat_tab_button",
                        min_width=0,
                    )

                # Settings go here
                gr.Checkbox(label="test")
            with gr.Tab(open=False, label="Contextual Compressors and Minifiers"):
                with gr.Row():
                    self.components["custom_special"] = gr.Dropdown(
                        value="Github",
                        choices=["Github", "Save to Topic Domain", "Don't Save"],
                        label="Source",
                        interactive=True,
                    )
                    self.components["test_special"] = gr.Button(
                        value="Test Loader",
                        variant="primary",
                        elem_classes="chat_tab_button",
                        min_width=0,
                    )

                # Settings go here
                gr.Checkbox(label="test")

            with gr.Tab(open=False, label="Save files and configs"):
                self.components["data_domain_drp"] = gr.Dropdown(
                    allow_custom_value=True,
                    value=self.the_context_index.index_data_domains[0].data_domain_name,
                    choices=[cls.data_domain_name for cls in self.the_context_index.index_data_domains],
                    show_label=False,
                    interactive=True,
                )
                self.components["data_source_drp"] = gr.Dropdown(
                    allow_custom_value=True,
                    value=self.the_context_index.index_data_domains[0].data_domain_sources[0].data_source_name,
                    choices=[
                        cls.data_source_name for cls in self.the_context_index.index_data_domains[0].data_domain_sources
                    ],
                    show_label=False,
                    interactive=True,
                )
            # self.url_or_files_radio_toggle()

    def add_data_domain(self):
        if data_domains := getattr(self.the_context_index, "data_domains", None):
            for data_domain in data_domains:
                if self.config.current_data_domain_name == data_domain.NAME:
                    self.current_data_domain_instance = data_domain
                    break
        if self.current_data_domain_instance is None:
            if data_domains is None:
                self.the_context_index.data_domains = []
            new_domain = DataDomain()
            self.the_context_index.data_domains.append(new_domain)  # type: ignore
            self.current_data_domain_instance = new_domain
            self.config.current_data_domain_name = new_domain.NAME

        with gr.Tab(label="Add Topic"):
            data_domain_components = {}

            new_domain_button = gr.Button(
                value="New Topic",
                variant="primary",
                min_width=0,
                size="sm",
            )

            data_domain_components["data_domains_dropdown"] = gr.Dropdown(
                value=self.config.current_data_domain_name,
                choices=self.context_index_service.list_context_class_names(self.the_context_index.data_domains),
                label="Available Topics",
                allow_custom_value=False,
            )
            data_domain_components["NAME"] = gr.Textbox(
                value=self.current_data_domain_instance.NAME,
                placeholder="Topic Name",
                show_label=False,
                lines=1,
                info="Rename your new or existing topic.",
            )
            data_domain_components["DESCRIPTION"] = gr.Textbox(
                value=self.current_data_domain_instance.DESCRIPTION,
                label="Topic Description",
                lines=1,
                info="Optional description of your topic.",
            )
            data_domain_components["default_database_provider"] = gr.Dropdown(
                value=self.current_data_domain_instance.default_database_provider,
                choices=self.database_service.list_of_module_ui_names,
                label="Default Database Provider",
                info="Sets default that can be overridden by individual sources.",
            )

            save_domain_button = gr.Button(
                value="Save Topic",
                variant="primary",
                min_width=0,
            )

            data_domain_components["delete_domain_confirmation"] = gr.Textbox(
                placeholder=f"Type {self.current_data_domain_instance.NAME} to confirm", lines=1, info="not implemented"
            )
            delete_domain_button = gr.Button(
                value="Delete selected Topic",
                variant="stop",
                min_width=0,
            )

            save_domain_button.click(
                fn=lambda *x: GradioHelper.update_config_classes(
                    self.current_data_domain_instance, data_domain_components, *x
                ),
                inputs=list(data_domain_components.values()),
            ).then(
                fn=self.set_current_data_domain,
                inputs=data_domain_components["data_domains_dropdown"],
                outputs=list(data_domain_components.values()),
            )

            new_domain_button.click(
                fn=self.new_data_domain,
                outputs=list(data_domain_components.values()),
            )

        data_domain_components["data_domains_dropdown"].change(
            fn=self.set_current_data_domain,
            inputs=data_domain_components["data_domains_dropdown"],
            outputs=list(data_domain_components.values()),
        )

    def new_data_domain(self):
        new_domain = DataDomain()
        self.the_context_index.data_domains.append(new_domain)
        return self.set_current_data_domain(new_domain.NAME)

    def set_current_data_domain(self, requested_instance_ui_name):
        for data_domain in self.the_context_index.data_domains:
            if requested_instance_ui_name == data_domain.NAME:
                self.current_data_domain_instance = data_domain
                break
        output = []

        output.append(
            gr.Dropdown(
                value=self.current_data_domain_instance.NAME,
                choices=self.context_index_service.list_context_class_names(self.the_context_index.data_domains),
            )
        )
        output.append(gr.Textbox(value=self.current_data_domain_instance.NAME))
        output.append(gr.Textbox(value=self.current_data_domain_instance.DESCRIPTION))
        output.append(gr.Dropdown(value=self.current_data_domain_instance.default_database_provider))
        output.append(gr.Textbox(placeholder=f"Type {self.current_data_domain_instance.NAME} to confirm"))

        return output

    def create_event_handlers(self):
        gr.on(
            triggers=[
                self.components["ingest_button"].click,
                self.components["url_textbox"].submit,
                self.components["file_path_textbox"].submit,
            ],
            inputs=list(self.components.values()),
            fn=lambda val: self.ingest_agent.ingest_from_ui(self.components, val),
        )
