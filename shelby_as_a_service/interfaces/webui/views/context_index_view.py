from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from agents.ingest.ingest_agent import IngestAgent
from app.module_base import ModuleBase
from index.context_index import ContextIndex
from index.context_index_model import (
    ContextModel,
    DocDBConfigs,
    DocIngestTemplateConfigs,
    DomainModel,
    SourceModel,
)
from pydantic import BaseModel
from services.document_db.document_db_service import DocumentDBService


class ContextIndexView(ModuleBase):
    CLASS_NAME: str = "context_index_view"
    CLASS_UI_NAME: str = "Context Index"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6
    # REQUIRED_CLASSES: list[Type] = [IngestAgent, DocumentDBService]

    class ClassConfigModel(BaseModel):
        current_domain_name: str = "default_data_domain"
        current_source_name: str = "default_data_source"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_ui_names: list
    list_of_class_instances: list
    ingest_agent: IngestAgent
    document_db_service: DocumentDBService

    context_index: ContextIndex
    # current_domain: DataDomain
    # current_source: DataSource

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)
        self.context_index = ContextIndex()
        self.ingest_agent = IngestAgent()
        self.document_db_service = DocumentDBService()

        self.components = {}

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
            with gr.Tab(label="Quick Add"):
                self.quick_add()
            with gr.Tab(label="Index Builder"):
                self.create_context_builder_tab()

            # self.create_event_handlers()
            with gr.Tab(label="Management"):
                self.document_db_service.create_settings_ui()

    def quick_add(self):
        self.components["ingest_button"] = gr.Button(
            value="Ingest",
            variant="primary",
            elem_classes="chat_tab_button",
            min_width=0,
        )
        self.components["url_textbox"] = gr.Textbox(
            placeholder="Web URL or Local Filepath (or drag and drop)",
            lines=1,
            show_label=False,
        )
        gr.Dropdown(
            value=self.context_index.domain.source.model.enabled_doc_ingest_template.ingest_template_name,
            choices=self.context_index.domain.source.list_of_ingest_template_names,
            label="Ingest Preset",
            allow_custom_value=False,
        )

        with gr.Row():
            self.components["domains_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.model.name,
                choices=self.context_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
            )
            self.components["sources_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.source.model.name,
                choices=self.context_index.domain.list_of_source_names,
                label="Current Source",
                allow_custom_value=False,
            )

            self.components["files_drop_box"] = gr.File(
                visible=True,
                label="Drag and drop file",
            )

    def create_context_builder_tab(self):
        with gr.Tab(label="Docs"):
            pass
        with gr.Tab(label="Sources"):
            self.create_builder_sources_tab()
        with gr.Tab(label="Topics"):
            self.create_builder_topics_tab()
        with gr.Tab(label="Batch Update Index"):
            self.components["ingest_button"] = gr.Button(
                value="Run Full Index Ingest Pipeline",
                variant="primary",
            )

    def create_builder_sources_tab(self):
        source_inputs = {}
        new_source_components = {}
        source_buttons = {}

        with gr.Row():
            source_inputs["domains_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.model.name,
                choices=self.context_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
            )
            source_inputs["sources_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.source.model.name,
                choices=self.context_index.domain.list_of_source_names,
                label="Current Source",
                allow_custom_value=False,
            )

        with gr.Row():
            source_buttons["save_source_button"] = gr.Button(
                value="Save Changes to this Source",
                variant="primary",
                min_width=0,
                size="sm",
            )

        with gr.Tab(label="Add New"):
            new_source_components["new_source_name"] = gr.Textbox(
                placeholder=self.context_index.domain.source.model.name,
                lines=1,
                container=True,
                label="New Source Name",
            )
            new_source_components["description"] = gr.Textbox(
                placeholder=self.context_index.domain.source.model.description,
                lines=1,
                container=True,
                label="New Source Description",
            )
            source_inputs["batch_update_enabled"] = gr.Checkbox(
                value=False,
                label="Clone Current Source",
                info="Not implemented. Currently uses defaults from models.",
            )
            source_buttons["new_source_button"] = gr.Button(
                value="Add New Source",
                variant="primary",
                min_width=0,
                size="sm",
            )
        with gr.Tab(label="Loader"):
            self.components["url_textbox"] = gr.Textbox(
                placeholder="Web URL or Local Filepath",
                lines=1,
                show_label=False,
            )
            self.ingest_agent.create_loader_ui(current_class=self.context_index.domain.source.model)
        with gr.Tab(label="Processor"):
            gr.Textbox(
                value="Not Implemented",
                show_label=False,
                lines=1,
            )
            # self.ingest_agent.create_processor_ui()

        with gr.Tab(label="Database"):
            source_inputs["database_provider"] = gr.Dropdown(
                value=self.context_index.domain.source.model.enabled_doc_db.db_name,
                choices=self.context_index.list_of_db_names,
                show_label=False,
                info="Default document database for the Souce. Database settings are managed elsewhere.",
            )

        with gr.Tab(label="Manage"):
            gr.Textbox(
                value="Not Implemented",
                show_label=False,
                lines=1,
            )
            gr.Dropdown(
                placeholder="Not Implemented",
                choices=["Not Implemented"],
            )
            with gr.Row():
                gr.Button(
                    value="Load Template",
                    variant="primary",
                    min_width=0,
                )
                gr.Button(
                    value="Save Template",
                    variant="primary",
                    min_width=0,
                )
            gr.Textbox(
                value=self.context_index.domain.source.model.name,
                label="New source Name",
                lines=1,
            )
            gr.Textbox(
                value=self.context_index.domain.source.model.description,
                label="New source Description",
                lines=1,
            )
            with gr.Row():
                gr.Textbox(
                    placeholder=f"Type {self.context_index.domain.source.model.name} to confirm deletion.",
                    lines=1,
                    show_label=False,
                )
                gr.Button(
                    value=f"Delete {self.context_index.domain.source.model.name} and all it's sources.",
                    min_width=0,
                    size="sm",
                    variant="stop",
                )
        with gr.Tab(label="Ingest Source"):
            source_inputs["batch_update_enabled"] = gr.Checkbox(
                value=self.context_index.domain.source.model.batch_update_enabled,
                label="Update Source During Topic Batch Update",
            )
            self.components["ingest_button"] = gr.Button(
                value="Run Full Source Ingest Pipeline",
                variant="primary",
            )
            self.components["test_loader_button"] = gr.Button(
                value="Test Loader",
                variant="primary",
            )
        self.components["source_inputs"] = source_inputs
        self.components["new_source_components"] = new_source_components
        self.components["source_buttons"] = source_buttons

    def create_builder_topics_tab(self):
        data_domain_inputs = {}
        new_domain_components = {}
        data_domain_buttons = {}

        with gr.Row():
            data_domain_inputs["domains_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.model.name,
                choices=self.context_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
            )

        with gr.Row():
            data_domain_buttons["save_domain_button"] = gr.Button(
                value="Save Changes to this topic",
                variant="primary",
                min_width=0,
                size="sm",
            )

        with gr.Tab(label="Add New"):
            new_domain_components["new_domain_name"] = gr.Textbox(
                placeholder=self.context_index.domain.model.name,
                lines=1,
                container=True,
                label="New Topic Name",
            )
            new_domain_components["description"] = gr.Textbox(
                placeholder=self.context_index.domain.model.description,
                lines=1,
                container=True,
                label="New Topic Description",
            )
            data_domain_inputs["batch_update_enabled"] = gr.Checkbox(
                value=False,
                label="Clone Current Topic",
                info="Not implemented. Currently uses defaults from models.",
            )
            data_domain_buttons["new_domain_button"] = gr.Button(
                value="Add New Topic",
                variant="primary",
                min_width=0,
                size="sm",
            )
        with gr.Tab(label="Loader"):
            self.ingest_agent.create_loader_ui(current_class=self.context_index.domain.model)
        with gr.Tab(label="Processor"):
            gr.Textbox(
                value="Not Implemented",
                show_label=False,
                lines=1,
            )
            # self.ingest_agent.create_processor_ui()

        with gr.Tab(label="Database"):
            data_domain_inputs["database_provider"] = gr.Dropdown(
                value=self.context_index.domain.model.enabled_doc_db.db_name,
                choices=self.context_index.list_of_db_names,
                show_label=False,
                info="Default document database for the topic. Database settings are managed elsewhere.",
            )

        with gr.Tab(label="Manage"):
            gr.Textbox(
                value="Not Implemented",
                show_label=False,
                lines=1,
            )
            gr.Dropdown(
                placeholder="Not Implemented",
                choices=["Not Implemented"],
            )
            with gr.Row():
                gr.Button(
                    value="Load Template",
                    variant="primary",
                    min_width=0,
                )
                gr.Button(
                    value="Save Template",
                    variant="primary",
                    min_width=0,
                )
            gr.Textbox(
                value=self.context_index.domain.model.name,
                label="New Domain Name",
                lines=1,
            )
            gr.Textbox(
                value=self.context_index.domain.model.description,
                label="New Domain Description",
                lines=1,
            )
            with gr.Row():
                gr.Textbox(
                    placeholder=f"Type {self.context_index.domain.model.name} to confirm deletion.",
                    lines=1,
                    show_label=False,
                )
                gr.Button(
                    value=f"Delete {self.context_index.domain.model.name} and all it's sources.",
                    min_width=0,
                    size="sm",
                    variant="stop",
                )
        with gr.Tab(label="Ingest Topic"):
            data_domain_inputs["batch_update_enabled"] = gr.Checkbox(
                value=self.context_index.domain.model.batch_update_enabled,
                label="Update Topic During Full Index Batch Update",
            )
            self.components["ingest_button"] = gr.Button(
                value="Run Full Topic Ingest Pipeline",
                variant="primary",
            )
            self.components["test_loader_button"] = gr.Button(
                value="Test Loader",
                variant="primary",
            )
        self.components["data_domain_inputs"] = data_domain_inputs
        self.components["new_domain_components"] = new_domain_components
        self.components["data_domain_buttons"] = data_domain_buttons

    def create_event_handlers(self):
        self.components["data_source_buttons"]["new_source_button"].click(
            fn=lambda name, description, database, batch, doc_loading: self.context_index.create_data_source(
                data_domain=self.context_index.current_domain,
                source_name=name,
                description=description,
                database_provider=database,
                batch_update_enabled=batch,
                doc_loading_provider=doc_loading,
            ),
            inputs=[
                self.components["new_source_components"]["new_source_name"],
                self.components["new_source_components"]["new_source_description"],
                self.components["new_source_components"]["new_source_database_provider"],
                self.components["new_source_components"]["new_source_batch_update_enabled"],
                self.components["new_source_components"]["new_source_doc_loading_provider"],
            ],
        ).then(
            fn=self.set_current_data_source,
            outputs=list(self.components["data_source_inputs"].values()),
        ).then(
            fn=lambda: ("", ""),
            outputs=[
                self.components["new_source_components"]["new_source_name"],
                self.components["new_source_components"]["new_source_description"],
            ],
        ).then(
            fn=lambda *x: GradioHelper.update_config_classes(
                self.context_index.current_domain.current_source.source_config,
                self.components["data_source_inputs"],
                *x,
            ),
            inputs=list(self.components["data_source_inputs"].values()),
        )

        self.components["data_source_buttons"]["save_source_button"].click(
            fn=lambda *x: GradioHelper.update_config_classes(
                self.context_index.current_domain.current_source.source_config,
                self.components["data_source_inputs"],
                *x,
            ),
            inputs=list(self.components["data_source_inputs"].values()),
        ).then(
            fn=self.set_current_data_source,
            inputs=self.components["data_source_inputs"]["sources_dropdown"],
            outputs=list(self.components["data_source_inputs"].values()),
        )

        self.components["data_source_inputs"]["domains_dropdown"].input(
            fn=self.set_current_data_domain,
            inputs=self.components["data_source_inputs"]["domains_dropdown"],
            outputs=list(self.components["data_domain_inputs"].values()),
        ).then(
            fn=self.set_current_data_source,
            outputs=list(self.components["data_source_inputs"].values()),
        )

        self.components["data_source_inputs"]["sources_dropdown"].input(
            fn=self.set_current_data_source,
            inputs=self.components["data_source_inputs"]["sources_dropdown"],
            outputs=list(self.components["data_source_inputs"].values()),
        )

        self.components["data_domain_buttons"]["new_domain_button"].click(
            fn=lambda name, description, database, batch, doc_loading: self.context_index.create_data_domain(
                domain_name=name,
                description=description,
                database_provider=database,
                batch_update_enabled=batch,
                doc_loading_provider=doc_loading,
            ),
            inputs=[
                self.components["new_domain_components"]["new_domain_name"],
                self.components["new_domain_components"]["new_domain_description"],
                self.components["new_domain_components"]["new_domain_database_provider"],
                self.components["new_domain_components"]["new_domain_batch_update_enabled"],
                self.components["new_domain_components"]["new_domain_doc_loading_provider"],
            ],
        ).then(
            fn=self.set_current_data_domain,
            outputs=list(self.components["data_domain_inputs"].values()),
        ).then(
            fn=lambda: ("", ""),
            outputs=[
                self.components["new_domain_components"]["new_domain_name"],
                self.components["new_domain_components"]["new_domain_description"],
            ],
        ).then(
            fn=self.set_current_data_source,
            outputs=list(self.components["data_source_inputs"].values()),
        ).then(
            fn=lambda *x: GradioHelper.update_config_classes(
                self.context_index.current_domain.domain_config,
                self.components["data_domain_inputs"],
                *x,
            ),
            inputs=list(self.components["data_domain_inputs"].values()),
        )

        self.components["data_domain_buttons"]["save_domain_button"].click(
            fn=lambda *x: GradioHelper.update_config_classes(
                self.context_index.current_domain.domain_config,
                self.components["data_domain_inputs"],
                *x,
            ),
            inputs=list(self.components["data_domain_inputs"].values()),
        ).then(
            fn=self.set_current_data_domain,
            inputs=self.components["data_domain_inputs"]["domains_dropdown"],
            outputs=list(self.components["data_domain_inputs"].values()),
        )

        self.components["data_domain_inputs"]["domains_dropdown"].input(
            fn=self.set_current_data_domain,
            inputs=self.components["data_domain_inputs"]["domains_dropdown"],
            outputs=list(self.components["data_domain_inputs"].values()),
        ).then(
            fn=self.set_current_data_source,
            outputs=list(self.components["data_source_inputs"].values()),
        )

        # gr.on(
        #     triggers=[
        #         self.components["ingest_button"].click,
        #         self.components["url_textbox"].submit,
        #         self.components["file_path_textbox"].submit,
        #     ],
        #     inputs=list(self.components.values()),
        #     fn=lambda val: self.ingest_agent.ingest_from_ui(self.components, val),
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
