from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from agents.ingest.ingest_agent import IngestAgent
from app.module_base import ModuleBase
from context_index.index_base import ContextIndexBase, DataDomain, DataSource
from pydantic import BaseModel
from services.database.database_service import DatabaseService


class ContextIndexView(ModuleBase):
    CLASS_NAME: str = "context_index_view"
    CLASS_UI_NAME: str = "Context Index"
    SETTINGS_UI_COL = 3
    PRIMARY_UI_COL = 7
    REQUIRED_CLASSES: list[Type] = [IngestAgent, DatabaseService]

    class ClassConfigModel(BaseModel):
        current_domain_name: str = "default_data_domain"
        current_source_name: str = "default_data_source"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_ui_names: list
    list_of_class_instances: list
    ingest_agent: IngestAgent
    database_service: DatabaseService

    context_index: ContextIndexBase
    current_domain: DataDomain
    current_source: DataSource

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)
        self.components = {}

        # for data_domain_name, data_domain in self.context_index.data_domains.items():
        #     if self.config.current_domain_name == data_domain_name:
        #         self.current_domain = data_domain
        #         break
        #     if getattr(self, "current_domain", None) is None:
        #         self.current_domain = data_domain
        #         self.config.current_domain_name = data_domain_name
        # for data_source_name, data_source in self.current_domain.data_sources.items():
        #     if self.config.current_source_name == data_source_name:
        #         self.current_source = data_source
        #         break
        #     if getattr(self, "current_source", None) is None:
        #         self.current_source = data_source
        #         self.config.current_source_name = data_source_name

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
            # self.create_data_source_tab()
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
                            value=self.context_index.index_data_domains[0].data_sources[0].data_source_name,
                            choices=[cls.data_source_name for cls in self.context_index.index_data_domains[0].data_sources],
                            show_label=False,
                            interactive=True,
                        )
                        self.components["default_local_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.context_index.index_data_domains[0].data_sources[0].data_source_name,
                            choices=[cls.data_source_name for cls in self.context_index.index_data_domains[0].data_sources],
                            show_label=False,
                            interactive=True,
                        )
                    with gr.Row():
                        self.components["custom_web_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.context_index.index_data_domains[0].data_sources[0].data_source_name,
                            choices=[cls.data_source_name for cls in self.context_index.index_data_domains[0].data_sources],
                            show_label=False,
                            interactive=True,
                        )
                        self.components["custom_local_data_source_drp"] = gr.Dropdown(
                            visible=False,
                            allow_custom_value=True,
                            value=self.context_index.index_data_domains[0].data_sources[0].data_source_name,
                            choices=[cls.data_source_name for cls in self.context_index.index_data_domains[0].data_sources],
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

            self.components["default_custom_checkbox"].input(
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

            self.components["url_or_file_radio"].input(
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
        def set_current_data_source(requested_instance_ui_name):
            self.context_index.get_requested_domain(requested_instance_ui_name)

            output = []

            output.append(
                gr.Dropdown(
                    value=self.context_index.index_config.current_domain_name,
                    choices=self.context_index.list_of_data_domain_ui_names,
                )
            )
            output.append(
                gr.Dropdown(
                    value=self.context_index.current_domain.current_source.source_config.name,
                    choices=self.context_index.current_domain.list_of_data_source_ui_names,
                )
            )
            output.append(gr.Textbox(value=self.context_index.current_domain.current_source.source_config.name))
            output.append(gr.Textbox(value=self.context_index.current_domain.current_source.source_config.description))
            output.append(
                gr.Dropdown(value=self.context_index.current_domain.current_source.source_config.database_provider)
            )
            output.append(
                gr.Checkbox(value=self.context_index.current_domain.current_source.source_config.batch_update_enabled)
            )
            output.append(
                gr.Textbox(
                    placeholder=f"Type {self.context_index.current_domain.current_source.source_config.name} to confirm deletion.
                )
            )

            return output

        with gr.Tab(label="Add Source"):
            data_source_components = {}

            data_source_components["data_domains_dropdown"] = gr.Dropdown(
                value=self.context_index.index_config.current_domain_name,
                choices=self.context_index.list_of_data_domain_ui_names,
                label="Available Topics",
                allow_custom_value=False,
            )

            new_source_button = gr.Button(
                value="New Source",
                variant="primary",
                min_width=0,
                size="sm",
            )
            data_source_components["data_sources_dropdown"] = gr.Dropdown(
                value=self.context_index.current_domain.domain_config.current_source_name,
                choices=self.context_index.current_domain.list_of_data_source_ui_names,
                label="Available Sources",
                allow_custom_value=False,
            )
            data_source_components["name"] = gr.Textbox(
                value=self.context_index.current_domain.current_source.source_config.name,
                placeholder="Source Name",
                show_label=False,
                lines=1,
                info="Rename your new or existing source.",
            )
            data_source_components["description"] = gr.Textbox(
                value=self.context_index.current_domain.current_source.source_config.description,
                label="Source Description",
                lines=1,
                info="Optional description of your source.",
            )
            data_source_components["default_doc_loader"] = gr.Dropdown(
                value=self.context_index.current_domain.current_source.source_config.doc_loading_provider,
                choices=self.database_service.list_of_class_ui_names,
                label="Default Document Loader",
                info="Sets default that can be overridden by individual documents.",
            )
            data_source_components["database_provider"] = gr.Dropdown(
                value=self.context_index.current_domain.current_source.source_config.database_provider,
                choices=self.database_service.list_of_class_ui_names,
                label="Default Database Provider",
                info="Sets default that can be overridden by individual documents.",
            )
            data_source_components["batch_update_enabled"] = gr.Checkbox(
                value=self.context_index.current_domain.current_source.source_config.batch_update_enabled,
                label="Batch Update Enabled",
            )

            save_source_button = gr.Button(
                value="Save Source",
                variant="primary",
                min_width=0,
            )
            data_source_components["delete_source_confirmation"] = gr.Textbox(
                placeholder=f"Type {self.context_index.current_domain.current_source.source_config.name} to confirm deletion.
                lines=1,
                info="not implemented",
            )
            delete_source_button = gr.Button(
                value="Delete selected Source",
                variant="stop",
                min_width=0,
            )

            save_source_button.click(
                fn=lambda *x: GradioHelper.update_config_classes(self.current_source, data_source_components, *x),
                inputs=list(data_source_components.values()),
            ).then(
                fn=set_current_data_source,
                inputs=data_source_components["data_sources_dropdown"],
                outputs=list(data_source_components.values()),
            )

            new_source_button.click(
                fn=self.context_index.create_data_source,
                outputs=list(data_source_components.values()),
            )

        data_source_components["data_sources_dropdown"].input(
            fn=set_current_data_source,
            inputs=data_source_components["data_sources_dropdown"],
            outputs=list(data_source_components.values()),
        )
        data_source_components["data_domains_dropdown"].input(
            fn=self.set_current_data_domain,
            inputs=data_source_components["data_domains_dropdown"],
            outputs=list(data_source_components.values()),
        )

    def create_data_domain_tab(self):
        data_domain_components = {}
        with gr.Tab(label="Topics"):
            data_domain_components["data_domains_dropdown"] = gr.Dropdown(
                value=self.context_index.index_config.current_domain_name,
                choices=self.context_index.list_of_data_domain_ui_names,
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

            with gr.Tab(label="Add Topic"):
                new_domain_components = {}
                new_domain_components["new_domain_name"] = gr.Textbox(
                    placeholder="Your New Topic Name",
                    show_label=False,
                    lines=1,
                )
                new_domain_components["new_domain_description"] = gr.Textbox(
                    value=self.context_index.current_domain.domain_config.description,
                    placeholder="Optional Topic Description",
                    show_label=False,
                    lines=1,
                )
                new_domain_components["new_domain_database_provider"] = gr.Dropdown(
                    value=self.context_index.current_domain.domain_config.database_provider,
                    choices=self.context_index.database_service.list_of_class_names,
                    label="Default Database Provider",
                    info="Sets default that can be overridden by individual sources.",
                )
                new_domain_components["new_domain_doc_loading_provider"] = gr.Dropdown(
                    value=self.context_index.current_domain.domain_config.doc_loading_provider,
                    choices=self.context_index.doc_loading_service.list_of_class_names,
                    label="Default Doc Loading Provider",
                    info="Sets default that can be overridden by individual sources.",
                )
                new_domain_components["new_domain_batch_update_enabled"] = gr.Checkbox(
                    value=self.context_index.current_domain.domain_config.batch_update_enabled,
                    label="Batch Update Enabled",
                )
                new_domain_button = gr.Button(
                    value="Add New Topic",
                    variant="primary",
                    min_width=0,
                    size="sm",
                )

            with gr.Tab(label="Manage Topics"):
                data_domain_components["name"] = gr.Textbox(
                    value=self.context_index.current_domain.domain_config.name,
                    placeholder="Topic Name",
                    show_label=False,
                    lines=1,
                    info="Rename your existing topic.",
                )
                data_domain_components["description"] = gr.Textbox(
                    value=self.context_index.current_domain.domain_config.description,
                    label="Topic Description",
                    lines=1,
                    info="Optional description of your topic.",
                )
                data_domain_components["database_provider"] = gr.Dropdown(
                    value=self.context_index.current_domain.domain_config.database_provider,
                    choices=self.context_index.database_service.list_of_class_names,
                    label="Default Database Provider",
                    info="Sets default that can be overridden by individual sources.",
                )
                data_domain_components["doc_loading_provider"] = gr.Dropdown(
                    value=self.context_index.current_domain.domain_config.doc_loading_provider,
                    choices=self.context_index.doc_loading_service.list_of_class_names,
                    label="Default Doc Loading Provider",
                    info="Sets default that can be overridden by individual sources.",
                )
                data_domain_components["batch_update_enabled"] = gr.Checkbox(
                    value=self.context_index.current_domain.domain_config.batch_update_enabled,
                    label="Batch Update Enabled",
                )
                save_domain_button = gr.Button(
                    value="Save Changes",
                    variant="primary",
                    min_width=0,
                )
                data_domain_components["delete_domain_confirmation"] = gr.Textbox(
                    placeholder=f"Type {self.context_index.current_domain.domain_config.name,} to confirm deletion.
                    lines=1,
                    info="not implemented",
                )
                delete_domain_button = gr.Button(
                    value="Delete selected Topic",
                    variant="stop",
                    min_width=0,
                )

                new_domain_button.click(
                    fn=lambda name, description, database, doc_loading, batch: self.context_index.create_data_domain(
                        domain_name=name,
                        description=description,
                        database_provider=database,
                        doc_loading_provider=doc_loading,
                        batch_update_enabled=batch,
                    ),
                    inputs=[
                        new_domain_components["new_domain_name"],
                        new_domain_components["new_domain_description"],
                        new_domain_components["new_domain_database_provider"],
                        new_domain_components["new_domain_doc_loading_provider"],
                        new_domain_components["new_domain_batch_update_enabled"],
                    ],
                ).then(
                    fn=self.set_current_data_domain,
                    outputs=list(data_domain_components.values()),
                ).then(
                    fn=lambda: ("", ""),
                    outputs=[new_domain_components["new_domain_name"], new_domain_components["new_domain_description"]],
                ).then(
                    fn=lambda *x: GradioHelper.update_config_classes(
                        self.context_index.current_domain.domain_config, data_domain_components, *x
                    ),
                    inputs=list(data_domain_components.values()
                )

            save_domain_button.click(
                fn=lambda *x: GradioHelper.update_config_classes(
                    self.context_index.current_domain.domain_config, data_domain_components, *x
                ),
                inputs=list(data_domain_components.values()),
            ).then(
                fn=self.set_current_data_domain,
                inputs=data_domain_components["data_domains_dropdown"],
                outputs=list(data_domain_components.values()),
            )

        data_domain_components["data_domains_dropdown"].input(
            fn=self.set_current_data_domain,
            inputs=data_domain_components["data_domains_dropdown"],
            outputs=list(data_domain_components.values()),
        )

    def set_current_data_domain(self, requested_instance_ui_name: Optional[str] = None):
        if not requested_instance_ui_name:
            requested_instance_ui_name = self.context_index.index_config.current_domain_name

        self.context_index.get_requested_domain(requested_instance_ui_name)
        output = []
        output.append(
            gr.Dropdown(
                value=self.context_index.index_config.current_domain_name,
                choices=self.context_index.list_of_data_domain_ui_names,
            )
        )
        output.append(gr.Textbox(value=self.context_index.current_domain.domain_config.name))
        output.append(gr.Textbox(value=self.context_index.current_domain.domain_config.description))
        output.append(gr.Dropdown(value=self.context_index.current_domain.domain_config.database_provider))
        output.append(gr.Dropdown(value=self.context_index.current_domain.domain_config.doc_loading_provider))
        output.append(gr.Checkbox(value=self.context_index.current_domain.domain_config.batch_update_enabled))
        output.append(gr.Textbox(placeholder=f"Type {self.context_index.current_domain.domain_config.name} to confirm deletion."))

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
