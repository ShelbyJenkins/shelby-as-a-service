from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from agents.ingest.ingest_agent import IngestAgent
from app.module_base import ModuleBase
from app_config.context_index.index_base import ContextIndexService, DataDomain, DataSource
from pydantic import BaseModel
from services.database.database_service import DatabaseService


class ContextIndexView(ModuleBase):
    CLASS_NAME: str = "context_index_view"
    CLASS_UI_NAME: str = "Context Index"
    SETTINGS_UI_COL = 3
    PRIMARY_UI_COL = 7
    REQUIRED_CLASSES: list[Type] = [IngestAgent, DatabaseService]

    class ClassConfigModel(BaseModel):
        current_data_domain_name: str = "default_data_domain"
        current_data_source_name: str = "default_data_source"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_CLASS_UI_NAMEs: list
    list_of_class_instances: list
    ingest_agent: IngestAgent
    database_service: DatabaseService

    context_index_service: ContextIndexService
    the_context_index: ContextIndexService.TheContextIndex
    current_data_domain_instance: DataDomain
    current_data_source_instance: DataSource

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)
        self.components = {}

        for data_domain in self.the_context_index.data_domains:
            if self.config.current_data_domain_name == data_domain.NAME:
                self.current_data_domain_instance = data_domain
                break
            if getattr(self, "current_data_domain_instance", None) is None:
                self.current_data_domain_instance = data_domain
                self.config.current_data_domain_name = data_domain.NAME
        for data_source in self.current_data_domain_instance.data_sources:
            if self.config.current_data_source_name == data_source.NAME:
                self.current_data_source_instance = data_source
                break
            if getattr(self, "current_data_source_instance", None) is None:
                self.current_data_source_instance = data_source
                self.config.current_data_source_name = data_source.NAME

    def create_primary_ui(self):
        with gr.Column(elem_classes="primary_ui_col"):
            self.components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {ContextIndexView.CLASS_UI_NAME}",
                elem_id="chat_tab_out_text",
                elem_classes="chat_tab_out_text_class",
                scale=7,
            )

        # self.create_event_handlers()

    def create_settings_ui(self):
        with gr.Column():
            # self.quick_add()
            self.create_data_source_tab()
            self.create_data_domain_tab()
            with gr.Tab(label="Management"):
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
                            value=self.the_context_index.index_data_domains[0].data_sources[0].data_source_name,
                            choices=[
                                cls.data_source_name for cls in self.the_context_index.index_data_domains[0].data_sources
                            ],
                            show_label=False,
                            interactive=True,
                        )
                        self.components["default_local_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.the_context_index.index_data_domains[0].data_sources[0].data_source_name,
                            choices=[
                                cls.data_source_name for cls in self.the_context_index.index_data_domains[0].data_sources
                            ],
                            show_label=False,
                            interactive=True,
                        )
                    with gr.Row():
                        self.components["custom_web_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.the_context_index.index_data_domains[0].data_sources[0].data_source_name,
                            choices=[
                                cls.data_source_name for cls in self.the_context_index.index_data_domains[0].data_sources
                            ],
                            show_label=False,
                            interactive=True,
                        )
                        self.components["custom_local_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.the_context_index.index_data_domains[0].data_sources[0].data_source_name,
                            choices=[
                                cls.data_source_name for cls in self.the_context_index.index_data_domains[0].data_sources
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
            with gr.Tab(label="Custom Text Processor"):
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
            with gr.Tab(label="Contextual Compressors and Minifiers"):
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

    def create_data_source_tab(self):
        def new_data_source():
            new_source = DataSource()
            self.current_data_domain_instance.data_sources.append(new_source)
            return set_current_data_source(new_source.NAME)

        def set_current_data_source(requested_instance_ui_name):
            for data_source in self.current_data_domain_instance.data_sources:
                if requested_instance_ui_name == data_source.NAME:
                    self.current_data_source_instance = data_source
                    break

            output = []

            output.append(
                gr.Dropdown(
                    value=self.current_data_domain_instance.NAME,
                    choices=self.context_index_service.list_context_class_names(self.the_context_index.data_domains),
                )
            )
            output.append(
                gr.Dropdown(
                    value=self.current_data_source_instance.NAME,
                    choices=self.context_index_service.list_context_class_names(
                        self.current_data_domain_instance.data_sources
                    ),
                )
            )
            output.append(gr.Textbox(value=self.current_data_source_instance.NAME))
            output.append(gr.Textbox(value=self.current_data_source_instance.DESCRIPTION))
            output.append(gr.Dropdown(value=self.current_data_source_instance.default_database_provider))
            output.append(gr.Checkbox(value=self.current_data_source_instance.batch_update_enabled))
            output.append(gr.Textbox(placeholder=f"Type {self.current_data_source_instance.NAME} to confirm"))

            return output

        with gr.Tab(label="Add Source"):
            data_source_components = {}

            data_source_components["data_domains_dropdown"] = gr.Dropdown(
                value=self.config.current_data_domain_name,
                choices=self.context_index_service.list_context_class_names(self.the_context_index.data_domains),
                label="Currently Selected Topic",
                allow_custom_value=False,
            )

            new_source_button = gr.Button(
                value="New Source",
                variant="primary",
                min_width=0,
                size="sm",
            )
            data_source_components["data_sources_dropdown"] = gr.Dropdown(
                value=self.config.current_data_source_name,
                choices=self.context_index_service.list_context_class_names(self.current_data_domain_instance.data_sources),
                label="Available Sources",
                allow_custom_value=False,
            )
            data_source_components["NAME"] = gr.Textbox(
                value=self.current_data_source_instance.NAME,
                placeholder="Source Name",
                show_label=False,
                lines=1,
                info="Rename your new or existing source.",
            )
            data_source_components["DESCRIPTION"] = gr.Textbox(
                value=self.current_data_source_instance.DESCRIPTION,
                label="Source Description",
                lines=1,
                info="Optional description of your source.",
            )
            data_source_components["default_doc_loader"] = gr.Dropdown(
                value=self.current_data_source_instance.default_doc_loader,
                choices=self.database_service.list_of_CLASS_UI_NAMEs,
                label="Default Document Loader",
                info="Sets default that can be overridden by individual documents.",
            )
            data_source_components["default_database_provider"] = gr.Dropdown(
                value=self.current_data_source_instance.default_database_provider,
                choices=self.database_service.list_of_CLASS_UI_NAMEs,
                label="Default Database Provider",
                info="Sets default that can be overridden by individual documents.",
            )
            data_source_components["batch_update_enabled"] = gr.Checkbox(
                value=self.current_data_source_instance.batch_update_enabled,
                label="Batch Update Enabled",
            )

            save_source_button = gr.Button(
                value="Save Source",
                variant="primary",
                min_width=0,
            )
            data_source_components["delete_source_confirmation"] = gr.Textbox(
                placeholder=f"Type {self.current_data_source_instance.NAME} to confirm", lines=1, info="not implemented"
            )
            delete_source_button = gr.Button(
                value="Delete selected Source",
                variant="stop",
                min_width=0,
            )

            save_source_button.click(
                fn=lambda *x: GradioHelper.update_config_classes(
                    self.current_data_source_instance, data_source_components, *x
                ),
                inputs=list(data_source_components.values()),
            ).then(
                fn=set_current_data_source,
                inputs=data_source_components["data_sources_dropdown"],
                outputs=list(data_source_components.values()),
            )

            new_source_button.click(
                fn=new_data_source,
                outputs=list(data_source_components.values()),
            )

        data_source_components["data_sources_dropdown"].change(
            fn=set_current_data_source,
            inputs=data_source_components["data_sources_dropdown"],
            outputs=list(data_source_components.values()),
        )
        data_source_components["data_domains_dropdown"].change(
            fn=self.set_current_data_domain,
            inputs=data_source_components["data_domains_dropdown"],
            outputs=list(data_source_components.values()),
        )

    def create_data_domain_tab(self):
        def new_data_domain():
            new_domain = DataDomain()
            self.the_context_index.data_domains.append(new_domain)
            return self.set_current_data_domain(new_domain.NAME)

        data_domain_components = {}
        with gr.Tab(label="Topics"):
            data_domain_components["data_domains_dropdown"] = gr.Dropdown(
                value=self.config.current_data_domain_name,
                choices=self.context_index_service.list_context_class_names(self.the_context_index.data_domains),
                label="Available Topics",
                allow_custom_value=False,
            )
            with gr.Tab(label="Topic Details"):
                gr.Textbox(value="some details about the files in this topic")
                ingest_domain_button = gr.Button(
                    value="Update/Ingest all sources in this domain",
                    variant="primary",
                    min_width=0,
                    size="sm",
                )
            with gr.Tab(label="Manage Topics"):
                new_domain_button = gr.Button(
                    value="New Topic",
                    variant="primary",
                    min_width=0,
                    size="sm",
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
                data_domain_components["batch_update_enabled"] = gr.Checkbox(
                    value=self.current_data_domain_instance.batch_update_enabled,
                    label="Batch Update Enabled",
                )
                save_domain_button = gr.Button(
                    value="Save Changes",
                    variant="primary",
                    min_width=0,
                )
                delete_domain_button = gr.Button(
                    value="Delete selected Topic",
                    variant="stop",
                    min_width=0,
                )
                data_domain_components["delete_domain_confirmation"] = gr.Textbox(
                    placeholder=f"Type {self.current_data_domain_instance.NAME} to confirm", lines=1, info="not implemented"
                )

            with gr.Tab(label="Default Databases"):
                data_domain_components["default_database_provider"] = gr.Dropdown(
                    value=self.current_data_domain_instance.default_database_provider,
                    choices=self.database_service.list_of_CLASS_UI_NAMEs,
                    label="Default Database Provider",
                    info="Sets default that can be overridden by individual sources.",
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
                fn=new_data_domain,
                outputs=list(data_domain_components.values()),
            )

        data_domain_components["data_domains_dropdown"].change(
            fn=self.set_current_data_domain,
            inputs=data_domain_components["data_domains_dropdown"],
            outputs=list(data_domain_components.values()),
        )

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
        output.append(gr.Checkbox(value=self.current_data_domain_instance.batch_update_enabled))
        output.append(gr.Textbox(placeholder=f"Type {self.current_data_domain_instance.NAME} to confirm"))
        output.append(gr.Dropdown(value=self.current_data_domain_instance.default_database_provider))

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
