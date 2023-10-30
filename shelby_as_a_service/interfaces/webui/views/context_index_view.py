import typing
from typing import Any, Dict, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.context_index.context_index import ContextIndex
from services.context_index.context_index_model import (
    ContextConfigModel,
    ContextIndexModel,
    DocDBModel,
    DomainModel,
    SourceModel,
)
from services.context_index.ingest import DocIngest
from services.database.database_service import DataBaseService


class ContextIndexView(ModuleBase):
    CLASS_NAME: str = "context_index_view"
    CLASS_UI_NAME: str = "Context Index"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6
    # REQUIRED_CLASSES: list[Type] = [DocIngest, DataBaseService]

    class ClassConfigModel(BaseModel):
        current_domain_name: str = "default_data_domain"
        current_source_name: str = "default_data_source"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_ui_names: list
    list_of_required_class_instances: list
    doc_ingest: DocIngest
    database_service: DataBaseService

    context_index: ContextIndex
    # current_domain: DataDomain
    # current_source: DataSource
    uic: dict[str, Any]

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

        self.doc_ingest = DocIngest()
        self.database_service = DataBaseService()

        self.uic = {}  # ui components

    def create_primary_ui(self):
        with gr.Column(elem_classes="primary_ui_col"):
            self.uic["chat_tab_out_text"] = gr.Textbox(
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
            with gr.Tab(label="Quick Add"):
                # self.quick_add()
                pass
            with gr.Tab(label="Context Builder"):
                self.create_context_builder_tab()

            # self.create_event_handlers()
            with gr.Tab(label="Management"):
                # self.document_db_service.create_settings_ui()
                pass

    def quick_add(self):
        self.uic["ingest_button"] = gr.Button(
            value="Ingest",
            variant="primary",
            elem_classes="chat_tab_button",
            min_width=0,
        )
        self.uic["url_textbox"] = gr.Textbox(
            placeholder="Web URL or Local Filepath (or drag and drop)",
            lines=1,
            show_label=False,
        )
        gr.Dropdown(
            value=self.context_index.domain.source.instance_model.enabled_doc_ingest_template.ingest_template_name,
            choices=self.context_index.domain.source.list_of_ingest_template_names,
            label="Ingest Preset",
            allow_custom_value=False,
        )

        with gr.Row():
            self.uic["domains_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.instance_model.name,
                choices=self.context_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
            )
            self.uic["sources_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.source.instance_model.name,
                choices=self.context_index.domain.list_of_source_names,
                label="Current Source",
                allow_custom_value=False,
            )

            self.uic["files_drop_box"] = gr.File(
                visible=True,
                label="Drag and drop file",
            )

    def create_context_builder_tab(self):
        cbc = {}  # context builder components
        with gr.Tab(label="Docs"):
            pass
        with gr.Tab(label="Sources"):
            cbc["sources"] = self.create_builder_sources_tab()
        with gr.Tab(label="Topics"):
            cbc["topics"] = self.create_builder_topics_tab()
        with gr.Tab(label="Batch Update Index"):
            cbc["ingest_button"] = gr.Button(
                value="Run Full Index Ingest Pipeline",
                variant="primary",
            )
        #   self.create_context_builder_event_handlers()

        self.uic["cbc"] = cbc

    def create_builder_sources_tab(self):
        inputs = {}
        context_template = {}
        buttons = {}

        with gr.Row():
            inputs["domains_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.instance_model.name,
                choices=self.context_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
            )
            inputs["sources_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.source.instance_model.name,
                choices=self.context_index.domain.list_of_source_names,
                label="Current Source",
                allow_custom_value=False,
            )

        with gr.Row():
            buttons["save_changes_button"] = gr.Button(
                value="Save Changes to this Source",
                variant="primary",
                min_width=0,
                size="sm",
            )

        with gr.Tab(label="Manage"):
            with gr.Accordion(label="New Source", open=True):
                buttons["make_new_button"] = gr.Button(
                    value="Add New Source",
                    variant="primary",
                    min_width=0,
                    size="sm",
                )
                inputs["make_new_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.instance_model.DEFAULT_SOURCE_NAME,
                    lines=1,
                    container=True,
                    label="New Source Name",
                )
                inputs["make_new_description"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.instance_model.DEFAULT_SOURCE_DESCRIPTION,
                    lines=1,
                    container=True,
                    label="New Source Description",
                )
                with gr.Row():
                    inputs["make_new_from_template_dropdown"] = gr.Dropdown(
                        value=self.context_index.domain.source.instance_model.DEFAULT_TEMPLATE_NAME,
                        choices=self.context_index.list_of_context_template_names,
                        label="Use Template",
                        allow_custom_value=False,
                    )
                    inputs["make_new_from_template_checkbox"] = gr.Checkbox(
                        value=False,
                        label="Use Selected Template",
                    )
                with gr.Accordion(label="Clone Existing Source", open=False):
                    with gr.Row():
                        inputs["make_new_from_clone_dropdown"] = gr.Dropdown(
                            value=self.context_index.domain.source.instance_model.name,
                            choices=self.context_index.list_of_all_context_index_source_names,
                            label="Available Sources",
                            allow_custom_value=False,
                        )
                        inputs["make_new_from_clone_checkbox"] = gr.Checkbox(
                            value=False,
                            label="Clone Selected Source",
                        )

            with gr.Accordion(label="Config Templates", open=False):
                inputs["load_template_dropdown"] = gr.Dropdown(
                    value=self.context_index.list_of_context_template_names[0],
                    choices=self.context_index.list_of_context_template_names,
                    label="Available Templates",
                    allow_custom_value=False,
                )
                buttons["load_template_button"] = gr.Button(
                    value="Load Template",
                    variant="primary",
                    min_width=0,
                )

                inputs["new_template_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.instance_model.name,
                    lines=1,
                    container=True,
                    label="New Template Name",
                )
                buttons["save_template_button"] = gr.Button(
                    value="Save as Template",
                    variant="primary",
                    min_width=0,
                )
            with gr.Accordion(label="Manage Current Source", open=False):
                inputs["delete_textbox"] = gr.Textbox(
                    placeholder=f"Type {self.context_index.domain.source.instance_model.name} to confirm deletion.",
                    lines=1,
                    show_label=False,
                )
                buttons["delete_button"] = gr.Button(
                    value=f"Delete {self.context_index.domain.source.instance_model.name}.",
                    min_width=0,
                    size="sm",
                    variant="stop",
                )
        with gr.Tab(label="Loader"):
            context_template["url_textbox"] = gr.Textbox(
                placeholder="Web URL or Local Filepath",
                lines=1,
                show_label=False,
            )
            self.doc_ingest.create_loader_ui(
                current_class=self.context_index.domain.source.instance_model
            )
        with gr.Tab(label="Processor"):
            gr.Textbox(
                value="Not Implemented",
                show_label=False,
                lines=1,
            )
            # self.doc_ingest.create_processor_ui()

        with gr.Tab(label="Database"):
            context_template["database_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.source.instance_model.context_config.doc_db.database_provider_name,
                choices=self.context_index.list_of_database_provider_names,
                show_label=False,
                info="Default document database for the Souce. Database context_template are managed elsewhere.",
            )

        with gr.Tab(label="Ingest Source"):
            context_template["batch_update_enabled"] = gr.Checkbox(
                value=self.context_index.domain.source.instance_model.context_config.batch_update_enabled,
                label="Update Source During Topic Batch Update",
            )
            buttons["ingest_button"] = gr.Button(
                value="Run Full Source Ingest Pipeline",
                variant="primary",
            )
            buttons["test_loader_button"] = gr.Button(
                value="Test Loader",
                variant="primary",
            )

        sources = {}
        sources["inputs"] = inputs
        sources["context_template"] = context_template
        sources["buttons"] = buttons

        return sources

    def create_builder_topics_tab(self):
        inputs = {}
        context_template = {}
        buttons = {}

        with gr.Row():
            inputs["domains_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.instance_model.name,
                choices=self.context_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
            )

        with gr.Row():
            buttons["save_changes_button"] = gr.Button(
                value="Save Changes to this topic",
                variant="primary",
                min_width=0,
                size="sm",
            )

        with gr.Tab(label="Manage"):
            with gr.Accordion(label="New Domain", open=True):
                buttons["make_new_button"] = gr.Button(
                    value="Add New Domain",
                    variant="primary",
                    min_width=0,
                    size="sm",
                )
                inputs["make_new_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.instance_model.DEFAULT_DOMAIN_NAME,
                    lines=1,
                    container=True,
                    label="New Domain Name",
                )
                inputs["make_new_description"] = gr.Textbox(
                    placeholder=self.context_index.domain.instance_model.DEFAULT_DOMAIN_DESCRIPTION,
                    lines=1,
                    container=True,
                    label="New Domain Description",
                )
                with gr.Row():
                    inputs["make_new_from_template_dropdown"] = gr.Dropdown(
                        value=self.context_index.domain.instance_model.DEFAULT_TEMPLATE_NAME,
                        choices=self.context_index.list_of_context_template_names,
                        label="Use Template",
                        allow_custom_value=False,
                    )
                    inputs["make_new_from_template_checkbox"] = gr.Checkbox(
                        value=False,
                        label="Use Selected Template",
                    )
                with gr.Accordion(label="Clone Existing Domain", open=False):
                    with gr.Row():
                        inputs["make_new_from_clone_dropdown"] = gr.Dropdown(
                            value=self.context_index.domain.instance_model.name,
                            choices=self.context_index.list_of_domain_names,
                            label="Available Domains",
                            allow_custom_value=False,
                        )
                        inputs["make_new_from_clone_checkbox"] = gr.Checkbox(
                            value=False,
                            label="Clone Selected Domain",
                        )

            with gr.Accordion(label="Config Templates", open=False):
                inputs["load_template_dropdown"] = gr.Dropdown(
                    value=self.context_index.list_of_context_template_names[0],
                    choices=self.context_index.list_of_context_template_names,
                    label="Available Templates",
                    allow_custom_value=False,
                )
                buttons["load_template_button"] = gr.Button(
                    value="Load Template",
                    variant="primary",
                    min_width=0,
                )

                inputs["new_template_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.instance_model.name,
                    lines=1,
                    container=True,
                    label="New Template Name",
                )
                buttons["save_template_button"] = gr.Button(
                    value="Save as Template",
                    variant="primary",
                    min_width=0,
                )
            with gr.Accordion(label="Manage Current Source", open=False):
                inputs["delete_textbox"] = gr.Textbox(
                    placeholder=f"Type {self.context_index.domain.instance_model.name} to confirm deletion.",
                    lines=1,
                    show_label=False,
                )
                buttons["delete_button"] = gr.Button(
                    value=f"Delete {self.context_index.domain.instance_model.name} and all it's sources.",
                    min_width=0,
                    size="sm",
                    variant="stop",
                )
        with gr.Tab(label="Loader"):
            self.doc_ingest.create_loader_ui(current_class=self.context_index.domain.instance_model)
        with gr.Tab(label="Processor"):
            gr.Textbox(
                value="Not Implemented",
                show_label=False,
                lines=1,
            )
            # self.doc_ingest.create_processor_ui()

        with gr.Tab(label="Database"):
            inputs["database_provider"] = gr.Dropdown(
                value=self.context_index.domain.instance_model.context_config.doc_db.database_provider_name,
                choices=self.context_index.list_of_database_provider_names,
                show_label=False,
                info="Default document database for the topic. Database context_template are managed elsewhere.",
            )
        with gr.Tab(label="Ingest Topic"):
            inputs["batch_update_enabled"] = gr.Checkbox(
                value=self.context_index.domain.instance_model.context_config.batch_update_enabled,
                label="Update Topic During Full Index Batch Update",
            )
            self.uic["ingest_button"] = gr.Button(
                value="Run Full Topic Ingest Pipeline",
                variant="primary",
            )
            self.uic["test_loader_button"] = gr.Button(
                value="Test Loader",
                variant="primary",
            )
        topics = {}
        topics["inputs"] = inputs
        topics["context_template"] = context_template
        topics["buttons"] = buttons

    def create_event_handlers(self):
        self.uic["data_buttons"]["make_new_button"].click(
            fn=lambda name, description, database, batch, doc_loading: self.context_index.create_data_source(
                data_domain=self.context_index.current_domain,
                source_name=name,
                description=description,
                database_provider=database,
                batch_update_enabled=batch,
                doc_loading_provider=doc_loading,
            ),
            inputs=[
                self.uic["context_template"]["new_source_name"],
                self.uic["context_template"]["new_source_description"],
                self.uic["context_template"]["new_source_database_provider"],
                self.uic["context_template"]["new_source_batch_update_enabled"],
                self.uic["context_template"]["new_source_doc_loading_provider"],
            ],
        ).then(
            fn=self.set_current_data_source,
            outputs=list(self.uic["data_inputs"].values()),
        ).then(
            fn=lambda: ("", ""),
            outputs=[
                self.uic["context_template"]["new_source_name"],
                self.uic["context_template"]["new_source_description"],
            ],
        ).then(
            fn=lambda *x: GradioHelper.update_config_classes(
                self.context_index.current_domain.current_source.source_config,
                self.uic["data_inputs"],
                *x,
            ),
            inputs=list(self.uic["data_inputs"].values()),
        )

        self.uic["data_buttons"]["save_source_button"].click(
            fn=lambda *x: GradioHelper.update_config_classes(
                self.context_index.current_domain.current_source.source_config,
                self.uic["data_inputs"],
                *x,
            ),
            inputs=list(self.uic["data_inputs"].values()),
        ).then(
            fn=self.set_current_data_source,
            inputs=self.uic["data_inputs"]["sources_dropdown"],
            outputs=list(self.uic["data_inputs"].values()),
        )

        self.uic["data_inputs"]["domains_dropdown"].input(
            fn=self.set_current_data_domain,
            inputs=self.uic["data_inputs"]["domains_dropdown"],
            outputs=list(self.uic["inputs"].values()),
        ).then(
            fn=self.set_current_data_source,
            outputs=list(self.uic["data_inputs"].values()),
        )

        self.uic["data_inputs"]["sources_dropdown"].input(
            fn=self.set_current_data_source,
            inputs=self.uic["data_inputs"]["sources_dropdown"],
            outputs=list(self.uic["data_inputs"].values()),
        )

        self.uic["buttons"]["new_domain_button"].click(
            fn=lambda name, description, database, batch, doc_loading: self.context_index.create_data_domain(
                domain_name=name,
                description=description,
                database_provider=database,
                batch_update_enabled=batch,
                doc_loading_provider=doc_loading,
            ),
            inputs=[
                self.uic["new_domain_components"]["new_domain_name"],
                self.uic["new_domain_components"]["new_domain_description"],
                self.uic["new_domain_components"]["new_domain_database_provider"],
                self.uic["new_domain_components"]["new_domain_batch_update_enabled"],
                self.uic["new_domain_components"]["new_domain_doc_loading_provider"],
            ],
        ).then(
            fn=self.set_current_data_domain,
            outputs=list(self.uic["inputs"].values()),
        ).then(
            fn=lambda: ("", ""),
            outputs=[
                self.uic["new_domain_components"]["new_domain_name"],
                self.uic["new_domain_components"]["new_domain_description"],
            ],
        ).then(
            fn=self.set_current_data_source,
            outputs=list(self.uic["data_inputs"].values()),
        ).then(
            fn=lambda *x: GradioHelper.update_config_classes(
                self.context_index.current_domain.domain_config,
                self.uic["inputs"],
                *x,
            ),
            inputs=list(self.uic["inputs"].values()),
        )

        self.uic["buttons"]["save_domain_button"].click(
            fn=lambda *x: GradioHelper.update_config_classes(
                self.context_index.current_domain.domain_config,
                self.uic["inputs"],
                *x,
            ),
            inputs=list(self.uic["inputs"].values()),
        ).then(
            fn=self.set_current_data_domain,
            inputs=self.uic["inputs"]["domains_dropdown"],
            outputs=list(self.uic["inputs"].values()),
        )

        self.uic["inputs"]["domains_dropdown"].input(
            fn=self.set_current_data_domain,
            inputs=self.uic["inputs"]["domains_dropdown"],
            outputs=list(self.uic["inputs"].values()),
        ).then(
            fn=self.set_current_data_source,
            outputs=list(self.uic["data_inputs"].values()),
        )

        # gr.on(
        #     triggers=[
        #         self.uic["ingest_button"].click,
        #         self.uic["url_textbox"].submit,
        #         self.uic["file_path_textbox"].submit,
        #     ],
        #     inputs=list(self.uic.values()),
        #     fn=lambda val: self.doc_ingest.ingest_from_ui(self.uic, val),
        # )

    def set_current_data_source(self, requested_instance_ui_name: Optional[str] = None):
        if not requested_instance_ui_name:
            requested_instance_ui_name = (
                self.context_index.current_domain.domain_config.current_source_name
            )

        self.context_index.get_requested_source(requested_instance_ui_name)
        output = []

        output.append(
            gr.Dropdown(
                value=self.context_index.index_config.current_domain_name,
                choices=self.context_index.list_of_data_domain_ui_names,
            )
        )
        output.append(
            gr.Dropdown(
                value=self.context_index.current_domain.domain_config.current_source_name,
                choices=self.context_index.current_domain.list_of_data_source_ui_names,
            )
        )
        output.append(
            gr.Textbox(value=self.context_index.current_domain.current_source.source_config.name)
        )
        output.append(
            gr.Textbox(
                value=self.context_index.current_domain.current_source.source_config.description
            )
        )
        output.append(
            gr.Dropdown(
                value=self.context_index.current_domain.current_source.source_config.database_provider
            )
        )
        output.append(
            gr.Checkbox(
                value=self.context_index.current_domain.current_source.source_config.batch_update_enabled
            )
        )
        output.append(
            gr.Dropdown(
                value=self.context_index.current_domain.current_source.source_config.doc_loading_provider
            )
        )
        output.append(
            gr.Textbox(
                placeholder=f"Type {self.context_index.current_domain.current_source.source_config.name} to confirm deletion."
            )
        )

        return output

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
        output.append(
            gr.Dropdown(value=self.context_index.current_domain.domain_config.database_provider)
        )
        output.append(
            gr.Checkbox(value=self.context_index.current_domain.domain_config.batch_update_enabled)
        )
        output.append(
            gr.Dropdown(value=self.context_index.current_domain.domain_config.doc_loading_provider)
        )
        output.append(
            gr.Textbox(
                placeholder=f"Type {self.context_index.current_domain.domain_config.name} to confirm deletion."
            )
        )

        return output
