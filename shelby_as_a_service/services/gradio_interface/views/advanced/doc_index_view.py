import time
from typing import Any, Literal, Optional, Type, get_args

import context_index.doc_index as doc_index_models
import gradio as gr
import services.gradio_interface.events.doc_index_events as doc_index_events
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService
from services.gradio_interface.gradio_base import GradioBase
from services.text_processing.ingest_processing.ingest_processing_service import (
    IngestProcessingService,
)


class DocIndexView(GradioBase):
    class_name = Literal["context_index_view"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Context Index"

    domain_tab_dict: dict[str, Any]
    source_tab_dict: dict[str, Any]
    domains_dd: gr.Dropdown
    sources_dd: gr.Dropdown

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

        self.uic: dict[str, Any] = {}  # ui components

    def set_view_event_handlers(self):
        doc_index_events.builder_event_handlers(uic=self.uic)

    def create_primary_ui(self):
        with gr.Column(elem_classes="primary_ui_col"):
            primary_ui = {}
            primary_ui["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {DocIndexView.CLASS_UI_NAME}",
                elem_id="chat_tab_out_text",
                elem_classes="chat_tab_out_text_class",
                scale=7,
                lines=30,
            )

            self.uic["primary_ui"] = primary_ui

    def create_settings_ui(self):
        with gr.Column():
            with gr.Tab(label="Quick Add"):
                # self.quick_add()
                pass
            with gr.Tab(label="Index Builder"):
                self.create_index_builder_tab()

    def create_index_builder_tab(self):
        self.uic["cbc"] = {}  # context builder components
        with gr.Row():
            self.uic["cbc"]["domains_dd"] = gr.Dropdown(
                value=self.doc_index.domain.name,
                choices=self.doc_index.domain_names,
                label="Current Domain",
                allow_custom_value=False,
                multiselect=False,
            )
            self.uic["cbc"]["sources_dd"] = gr.Dropdown(
                value=self.doc_index.source.name,
                choices=self.doc_index.domain.source_names,
                label="Current Source",
                allow_custom_value=False,
                multiselect=False,
            )

        with gr.Tab(label="Sources"):
            self.uic["cbc"]["source_tab_dict"] = self.create_builder_domain_or_source_tab(
                domain_or_source=doc_index_models.SourceModel
            )

        with gr.Tab(label="Topics"):
            self.uic["cbc"]["domain_tab_dict"] = self.create_builder_domain_or_source_tab(
                domain_or_source=doc_index_models.DomainModel
            )

        with gr.Tab(label="Batch Update Index"):
            gr.Button(
                value="Run Full Index Ingest Pipeline",
                variant="primary",
            )

    def create_builder_domain_or_source_tab(
        self,
        domain_or_source: Type[doc_index_models.DomainModel] | Type[doc_index_models.SourceModel],
    ):
        input_components = {}
        buttons = {}
        services_components = {}
        domain_or_source_config = {}
        dropdowns = {}

        if domain_or_source is doc_index_models.DomainModel:
            parent_instance = self.doc_index.domain
            parent_instance_name_str = "Domain"

        elif domain_or_source is doc_index_models.SourceModel:
            parent_instance = self.doc_index.source
            parent_instance_name_str = "Source"

        else:
            raise ValueError(
                f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
            )

        with gr.Row():
            buttons["save_changes_button"] = gr.Button(
                value="Save Changes to this topic",
                variant="primary",
                min_width=0,
                size="sm",
            )

        with gr.Tab(label="Manage"):
            with gr.Accordion(label=f"New {parent_instance_name_str}", open=True):
                buttons["make_new_button"] = gr.Button(
                    value=f"Add New {parent_instance_name_str}",
                    variant="primary",
                    min_width=0,
                    size="sm",
                )
                input_components["make_new_name"] = gr.Textbox(
                    placeholder=parent_instance.DEFAULT_NAME,
                    lines=1,
                    container=True,
                    label=f"New {parent_instance_name_str} Name",
                )
                input_components["make_new_description"] = gr.Textbox(
                    placeholder=parent_instance.DEFAULT_DESCRIPTION,
                    lines=1,
                    container=True,
                    label=f"New {parent_instance_name_str} Description",
                )
                with gr.Row():
                    input_components["make_new_from_template_dropdown"] = gr.Dropdown(
                        value=parent_instance.DEFAULT_TEMPLATE_NAME,
                        choices=self.doc_index.index.list_of_doc_index_template_names,
                        label="Use Template",
                        allow_custom_value=False,
                    )
                    input_components["make_new_from_template_checkbox"] = gr.Checkbox(
                        value=False,
                        label="Use Selected Template",
                    )
                    input_components["make_new_from_clone_checkbox"] = gr.Checkbox(
                        value=False,
                        label=f"Clone Current {parent_instance_name_str}",
                    )

            with gr.Accordion(label="Config Templates", open=False):
                input_components["load_template_dropdown"] = gr.Dropdown(
                    value=self.doc_index.index.list_of_doc_index_template_names[0],
                    choices=self.doc_index.index.list_of_doc_index_template_names,
                    label="Available Templates",
                    allow_custom_value=False,
                )
                buttons["load_template_button"] = gr.Button(
                    value="Load Template",
                    variant="primary",
                    min_width=0,
                )

                input_components["new_template_name"] = gr.Textbox(
                    placeholder=parent_instance.name,
                    lines=1,
                    container=True,
                    label="New Template Name",
                )
                buttons["save_template_button"] = gr.Button(
                    value="Save as Template",
                    variant="primary",
                    min_width=0,
                )

            with gr.Accordion(label="Manage Current Topic", open=False):
                domain_or_source_config["update_name"] = gr.Textbox(
                    placeholder=parent_instance.name,
                    lines=1,
                    container=True,
                    label=f"New {parent_instance_name_str} Name",
                    elem_id="update_name",
                )
                domain_or_source_config["update_description"] = gr.Textbox(
                    placeholder=parent_instance.description,
                    lines=1,
                    container=True,
                    label=f"New {parent_instance_name_str} Description",
                    elem_id="update_description",
                )
                buttons["delete_button"] = gr.Button(
                    value=f"Delete {parent_instance_name_str} and all it's configs and documents.",
                    min_width=0,
                    size="sm",
                    variant="stop",
                )
                input_components["delete_textbox"] = gr.Textbox(
                    placeholder=f"Type {parent_instance_name_str} Name to confirm deletion.",
                    lines=1,
                    show_label=False,
                )
        with gr.Tab(label="Loader"):
            if isinstance(parent_instance, doc_index_models.SourceModel):
                domain_or_source_config["source_uri"] = gr.Textbox(
                    value=parent_instance.source_uri,
                    label="Source URI",
                    elem_id="source_uri",
                    placeholder="URL or Filepath",
                )
            (
                doc_loaders_dd,
                doc_loader_components_dict,
            ) = DocLoadingService.create_doc_index_ui_components(
                parent_instance=parent_instance,
                groups_rendered=False,
            )
            dropdowns["doc_loaders_dd"] = doc_loaders_dd
            services_components["doc_loaders"] = doc_loader_components_dict

        with gr.Tab(label="Ingest Processor"):
            (
                doc_ingest_proc_dd,
                doc_ingest_processor_components_dict,
            ) = IngestProcessingService.create_doc_index_ui_components(
                parent_instance=parent_instance,
                groups_rendered=False,
            )
            dropdowns["doc_ingest_proc_dd"] = doc_ingest_proc_dd
            services_components["doc_ingest_procs"] = doc_ingest_processor_components_dict

        with gr.Tab(label="Database"):
            (
                doc_dbs_dd,
                doc_dbs_components_dict,
            ) = DatabaseService.create_doc_index_ui_components(
                parent_instance=parent_instance,
                groups_rendered=False,
            )
            dropdowns["doc_dbs_dd"] = doc_dbs_dd
            services_components["doc_dbs"] = doc_dbs_components_dict

        with gr.Tab(label=f"Ingest {parent_instance_name_str}"):
            domain_or_source_config["batch_update_enabled"] = gr.Checkbox(
                value=parent_instance.batch_update_enabled,
                label=f"Update {parent_instance_name_str} During Full Index Batch Update",
                elem_id="batch_update_enabled",
            )
            buttons["ingest_button"] = gr.Button(
                value=f"Run Full {parent_instance_name_str} Ingest Pipeline",
                variant="primary",
            )
            buttons["clear_domain_or_source"] = gr.Button(
                value=f"Clear all documents of {parent_instance_name_str}",
                variant="primary",
            )

        output = {}
        output["dropdowns"] = dropdowns
        output["domain_or_source_config"] = domain_or_source_config
        output["input_components"] = input_components
        output["services_components"] = services_components
        output["buttons"] = buttons
        return output

    def create_management_tab_event_handlers(self, ui_components, save_button):
        for name, component_dict in ui_components.items():
            self.set_components_elem_id_and_classes(
                provider_config_components=component_dict,
                provider_name=name,
                service_name=DatabaseService.CLASS_NAME,
            )
        save_button.click(
            fn=lambda *x: doc_index_events.save_provider_settings(
                provider_config_components_values=x,
            ),
            inputs=set(ui_components["pinecone_database"].values()),
        )
