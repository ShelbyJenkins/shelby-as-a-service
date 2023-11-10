import typing
from typing import Any, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from pydantic import BaseModel
from services.context_index.context_index import ContextIndex
from services.context_index.doc_index_model import (
    DocDBModel,
    DocIndexModel,
    DocIngestProcessorModel,
    DocLoaderModel,
    DomainModel,
    SourceModel,
)
from services.context_index.ingest import DocIngest
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService
from services.service_base import ServiceBase
from services.text_processing.ingest_processing.ingest_processing_service import (
    IngestProcessingService,
)


class ContextIndexView(ServiceBase):
    CLASS_NAME: str = "context_index_view"
    CLASS_UI_NAME: str = "Context Index"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6

    class ClassConfigModel(BaseModel):
        current_domain_name: str = "default_data_domain"
        current_source_name: str = "default_data_source"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    list_of_class_ui_names: list
    list_of_required_class_instances: list
    doc_ingest: Type[DocIngest]
    doc_ingest_processor_service: Type[IngestProcessingService]
    doc_loader_service: Type[DocLoadingService]
    database_service: Type[DatabaseService]
    context_index: ContextIndex

    uic: dict[str, Any]
    domain_tab_dict: dict[str, Any]
    source_tab_dict: dict[str, Any]
    domains_dd: gr.Dropdown
    sources_dd: gr.Dropdown

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        super().__init__(config=config, **kwargs)

        self.doc_loader_service = DocLoadingService
        self.database_service = DatabaseService
        self.doc_ingest_processor_service = IngestProcessingService
        self.doc_ingest = DocIngest

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

            with gr.Tab(label="Management"):
                save_button = gr.Button(value="Save Changes", variant="primary", min_width=0)
                ui_components = self.database_service.create_service_management_settings_ui()
                self.create_management_tab_event_handlers(ui_components, save_button)

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
            value=self.context_index.domain.source.object_model.enabled_doc_ingest_template.ingest_template_name,
            choices=self.context_index.domain.source.list_of_ingest_template_names,
            label="Ingest Preset",
            allow_custom_value=False,
        )

        with gr.Row():
            self.uic["domains_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.object_model.name,
                choices=self.context_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
            )
            self.uic["sources_dropdown"] = gr.Dropdown(
                value=self.context_index.domain.source.object_model.name,
                choices=self.context_index.domain.list_of_source_names,
                label="Current Source",
                allow_custom_value=False,
            )

            self.uic["files_drop_box"] = gr.File(
                visible=True,
                label="Drag and drop file",
            )

    def create_context_builder_tab(self):
        self.uic["cbc"] = {}  # context builder components
        with gr.Row():
            self.domains_dd = gr.Dropdown(
                value=self.context_index.domain.name,
                choices=self.context_index.list_of_all_context_index_domain_names,
                label="Current Domain",
                allow_custom_value=False,
                multiselect=False,
            )
            self.sources_dd = gr.Dropdown(
                value=self.context_index.source.name,
                choices=self.context_index.domain.list_of_source_names,
                label="Current Source",
                allow_custom_value=False,
                multiselect=False,
            )

        with gr.Tab(label="Docs"):
            pass
        with gr.Tab(label="Sources"):
            self.source_tab_dict = self.create_builder_domain_or_source_tab(
                domain_or_source=SourceModel
            )
            self.create_service_provider_select_events(
                domain_or_source=SourceModel,
                dropdowns=self.source_tab_dict["dropdowns"],
            )
        with gr.Tab(label="Topics"):
            self.domain_tab_dict = self.create_builder_domain_or_source_tab(
                domain_or_source=DomainModel
            )
            self.create_service_provider_select_events(
                domain_or_source=DomainModel,
                dropdowns=self.domain_tab_dict["dropdowns"],
            )
        with gr.Tab(label="Batch Update Index"):
            gr.Button(
                value="Run Full Index Ingest Pipeline",
                variant="primary",
            )

        self.create_builder_event_handlers()

    def create_builder_domain_or_source_tab(
        self, domain_or_source: Union[Type[DomainModel], Type[SourceModel]]
    ):
        input_components = {}
        buttons = {}
        services_components = {}
        domain_or_source_config = {}
        dropdowns = {}

        if domain_or_source is DomainModel:
            parent_instance = self.context_index.domain
            parent_instance_name_str = "Domain"

        elif domain_or_source is SourceModel:
            parent_instance = self.context_index.source
            parent_instance_name_str = "Source"

        else:
            raise ValueError(f"domain_or_source must be DomainModel or SourceModel")

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
                        choices=self.context_index.index.list_of_doc_index_template_names,
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
                    value=self.context_index.index.list_of_doc_index_template_names[0],
                    choices=self.context_index.index.list_of_doc_index_template_names,
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
            if isinstance(parent_instance, SourceModel):
                domain_or_source_config["source_uri"] = gr.Textbox(
                    value=parent_instance.source_uri,
                    label="Source URI",
                    elem_id="source_uri",
                    placeholder="URL or Filepath",
                )
            (
                doc_loaders_dd,
                doc_loader_components_dict,
            ) = self.doc_loader_service.create_service_ui_components(
                parent_instance=parent_instance,
                groups_rendered=False,
            )
            dropdowns["doc_loaders_dd"] = doc_loaders_dd
            services_components["doc_loaders"] = doc_loader_components_dict

        with gr.Tab(label="Ingest Processor"):
            (
                doc_ingest_proc_dd,
                doc_ingest_processor_components_dict,
            ) = self.doc_ingest_processor_service.create_service_ui_components(
                parent_instance=parent_instance,
                groups_rendered=False,
            )
            dropdowns["doc_ingest_proc_dd"] = doc_ingest_proc_dd
            services_components["doc_ingest_procs"] = doc_ingest_processor_components_dict

        with gr.Tab(label="Database"):
            (
                doc_dbs_dd,
                doc_dbs_components_dict,
            ) = self.database_service.create_service_ui_components(
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
            self.uic["ingest_button"] = gr.Button(
                value=f"Run Full {parent_instance_name_str} Ingest Pipeline",
                variant="primary",
            )
            self.uic["test_loader_button"] = gr.Button(
                value="Test Loader",
                variant="primary",
            )

        output = {}
        output["dropdowns"] = dropdowns
        output["domain_or_source_config"] = domain_or_source_config
        output["input_components"] = input_components
        output["services_components"] = services_components
        output["buttons"] = buttons
        return output

    def update_services_and_providers(self, parent_instance: Union[DomainModel, SourceModel]):
        services_components = {}
        (
            _,
            doc_loader_components_dict,
        ) = self.doc_loader_service.create_service_ui_components(
            parent_instance=parent_instance,
            groups_rendered=True,
        )
        services_components["doc_loaders"] = doc_loader_components_dict
        (
            _,
            doc_ingest_processor_components_dict,
        ) = self.doc_ingest_processor_service.create_service_ui_components(
            parent_instance=parent_instance,
            groups_rendered=False,
        )
        services_components["doc_ingest_procs"] = doc_ingest_processor_components_dict
        (
            _,
            doc_dbs_components_dict,
        ) = self.database_service.create_service_ui_components(
            parent_instance=parent_instance,
            groups_rendered=True,
        )
        services_components["doc_dbs"] = doc_dbs_components_dict

        return GradioHelpers.list_provider_config_components(services_components)

    def create_builder_event_handlers(self):
        def update_domain_or_source_tab_config_components(
            domain_or_source: Union[Type[DomainModel], Type[SourceModel]],
            set_instance_name: str,
        ) -> list:
            output = []

            if domain_or_source is DomainModel:
                parent_instance = self.context_index.get_domain_instance(name=set_instance_name)
                self.context_index.index.current_domain = parent_instance
            elif domain_or_source is SourceModel:
                parent_instance = self.context_index.get_source_instance(
                    name=set_instance_name,
                    parent_domain=self.context_index.domain,
                )
                self.context_index.domain.current_source = parent_instance
                ContextIndex.session.flush()

            else:
                raise ValueError(f"domain_or_source must be DomainModel or SourceModel")

            output.append(gr.Textbox(placeholder=parent_instance.name))
            output.append(gr.Textbox(placeholder=parent_instance.description))
            output.append(gr.Checkbox(value=parent_instance.batch_update_enabled))

            return output

        self.domains_dd.change(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
                parent_domain=self.context_index.domain,
            ),
            inputs=set(
                GradioHelpers.list_provider_config_components(
                    self.domain_tab_dict["services_components"]
                )
            ),
        ).success(
            fn=lambda *x: save_domain_or_source_config_settings(
                domain_or_source_config_values=x,
                parent_domain=self.context_index.domain,
            ),
            inputs=set(self.domain_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda x: update_domain_or_source_tab_config_components(
                domain_or_source=DomainModel,
                set_instance_name=x,
            ),
            inputs=self.domains_dd,
            outputs=list(self.domain_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda: self.update_services_and_providers(
                parent_instance=self.context_index.domain
            ),
            outputs=GradioHelpers.list_provider_config_components(
                self.domain_tab_dict["services_components"]
            ),
        ).success(
            fn=lambda: update_domain_or_source_dd(SourceModel),
            outputs=[self.sources_dd],
        )

        self.sources_dd.change(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
                parent_source=self.context_index.source,
            ),
            inputs=set(
                GradioHelpers.list_provider_config_components(
                    self.source_tab_dict["services_components"]
                )
            ),
        ).success(
            fn=lambda *x: save_domain_or_source_config_settings(
                domain_or_source_config_values=x,
                parent_source=self.context_index.source,
            ),
            inputs=set(self.source_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda x: update_domain_or_source_tab_config_components(
                domain_or_source=SourceModel,
                set_instance_name=x,
            ),
            inputs=self.sources_dd,
            outputs=list(self.source_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda: self.update_services_and_providers(
                parent_instance=self.context_index.source
            ),
            outputs=GradioHelpers.list_provider_config_components(
                self.source_tab_dict["services_components"]
            ),
        )

        self.domain_tab_dict["buttons"]["make_new_button"].click(
            fn=lambda *x: create_new_domain_or_source(
                domain_or_source=DomainModel,
                input_components=self.domain_tab_dict["input_components"],
                component_values=x,
            ),
            inputs=list(self.domain_tab_dict["input_components"].values()),
        ).success(fn=lambda: update_domain_or_source_dd(DomainModel), outputs=[self.domains_dd])
        self.source_tab_dict["buttons"]["make_new_button"].click(
            fn=lambda *x: create_new_domain_or_source(
                domain_or_source=SourceModel,
                input_components=self.source_tab_dict["input_components"],
                component_values=x,
            ),
            inputs=list(self.source_tab_dict["input_components"].values()),
        ).success(fn=lambda: update_domain_or_source_dd(SourceModel), outputs=[self.sources_dd])
        self.domain_tab_dict["buttons"]["save_changes_button"].click(
            fn=lambda *x: save_domain_or_source_config_settings(
                domain_or_source_config_values=x,
                parent_domain=self.context_index.domain,
            ),
            inputs=set(self.domain_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
                parent_domain=self.context_index.domain,
            ),
            inputs=set(
                GradioHelpers.list_provider_config_components(
                    self.domain_tab_dict["services_components"]
                )
            ),
        )
        self.source_tab_dict["buttons"]["save_changes_button"].click(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
                parent_source=self.context_index.source,
            ),
            inputs=set(
                GradioHelpers.list_provider_config_components(
                    self.source_tab_dict["services_components"]
                )
            ),
        ).success(
            fn=lambda *x: save_domain_or_source_config_settings(
                domain_or_source_config_values=x,
                parent_source=self.context_index.source,
            ),
            inputs=set(self.source_tab_dict["domain_or_source_config"].values()),
        )

        def create_new_domain_or_source(
            domain_or_source: Union[Type[DomainModel], Type[SourceModel]],
            input_components,
            component_values,
        ):
            if domain_or_source is DomainModel:
                create = self.context_index.create_domain
                clone_name = self.context_index.domain.name
                set_current = lambda instance: setattr(
                    self.context_index.index, "current_domain", instance
                )
            elif domain_or_source is SourceModel:
                create = lambda **kwargs: self.context_index.create_source(
                    parent_domain=self.context_index.domain, **kwargs
                )
                clone_name = self.context_index.source.name
                set_current = lambda instance: setattr(
                    self.context_index.domain, "current_source", instance
                )
            else:
                raise ValueError(f"domain_or_source must be DomainModel or SourceModel")

            ui_state = {k: v for k, v in zip(input_components.keys(), component_values)}

            from_template = ui_state.get("make_new_from_template_checkbox", False)
            from_clone = ui_state.get("make_new_from_clone_checkbox", False)
            if from_template and from_clone:
                gr.Warning(
                    "Cannot use both template and clone to create new domain. Defaulting to clone."
                )

            if from_clone:
                new_instance = create(
                    new_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                    clone_name=clone_name,
                )
            elif from_template:
                new_instance = create(
                    new_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                    requested_template_name=ui_state.get("make_new_from_template_dropdown", None),
                )
            else:
                new_instance = create(
                    new_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                )

            set_current(new_instance)
            ContextIndex.commit_context_index()

        def save_domain_or_source_config_settings(
            domain_or_source_config_values,
            parent_domain: Optional[DomainModel] = None,
            parent_source: Optional[SourceModel] = None,
        ):
            if parent_domain and parent_source:
                raise ValueError("parent_domain and parent_source cannot both be not None")
            parent_instance = parent_domain or parent_source
            for component, component_value in domain_or_source_config_values[0].items():
                if hasattr(parent_instance, component.elem_id):
                    setattr(parent_instance, component.elem_id, component_value)
            gr.Info(f"Saved Changes to {self.context_index.source.name}")

        def update_domain_or_source_dd(
            domain_or_source: Union[Type[DomainModel], Type[SourceModel]],
        ):
            if domain_or_source is DomainModel:
                return gr.update(
                    value=self.context_index.domain.name,
                    choices=self.context_index.list_of_all_context_index_domain_names,
                )
            elif domain_or_source is SourceModel:
                return gr.update(
                    value=self.context_index.source.name,
                    choices=self.context_index.domain.list_of_source_names,
                )
            else:
                raise ValueError(f"domain_or_source must be DomainModel or SourceModel")

    def create_service_provider_select_events(
        self,
        domain_or_source: Union[Type[DomainModel], Type[SourceModel]],
        dropdowns: dict,
    ):
        def select_enabled_provider_event(
            provider_select_dd: gr.Dropdown,
            set_model_type: Union[
                Type[DocDBModel], Type[DocLoaderModel], Type[DocIngestProcessorModel]
            ],
        ):
            provider_select_dd.input(
                fn=lambda x: self.context_index.set_current_domain_or_source_provider_instance(
                    domain_or_source=domain_or_source,
                    set_model_type=set_model_type,
                    set_name=x,
                ),
                inputs=provider_select_dd,
            )

        select_enabled_provider_event(dropdowns["doc_loaders_dd"], DocLoaderModel)
        select_enabled_provider_event(dropdowns["doc_ingest_proc_dd"], DocIngestProcessorModel)
        select_enabled_provider_event(dropdowns["doc_dbs_dd"], DocDBModel)

    def save_provider_settings(
        self,
        provider_config_components_values,
        parent_domain: Optional[DomainModel] = None,
        parent_source: Optional[SourceModel] = None,
    ):
        for component, component_value in provider_config_components_values[0].items():
            self.save_component_value_to_provider_config_dict(
                parent_domain=parent_domain,
                parent_source=parent_source,
                service_name=component.elem_classes[0],
                provider_name=component.elem_classes[1],
                provider_config_key=component.elem_id,
                component_value=component_value,
            )
        ContextIndex.commit_context_index()

    def save_component_value_to_provider_config_dict(
        self,
        parent_domain: Optional[DomainModel],
        parent_source: Optional[SourceModel],
        service_name: str,
        provider_name: str,
        provider_config_key: str,
        component_value: Any,
    ):
        match service_name:
            case DocLoadingService.CLASS_NAME:
                provider_model = self.context_index.get_or_create_doc_loader_instance(
                    parent_domain=parent_domain,
                    parent_source=parent_source,
                    name=provider_name,
                )
            case IngestProcessingService.CLASS_NAME:
                provider_model = self.context_index.get_or_create_doc_ingest_processor_instance(
                    parent_domain=parent_domain,
                    parent_source=parent_source,
                    name=provider_name,
                )
            case DatabaseService.CLASS_NAME:
                provider_model = self.context_index.get_or_create_doc_db_instance(
                    name=provider_name,
                )
            case _:
                raise ValueError(
                    f"service_name must be {DocLoadingService.CLASS_NAME}, {IngestProcessingService.CLASS_NAME}, or {DatabaseService.CLASS_NAME}"
                )

        if hasattr(provider_model, "config"):
            if provider_model.config.get(provider_config_key, None):
                provider_model.config[provider_config_key] = component_value

    def create_management_tab_event_handlers(self, ui_components, save_button):
        for name, component_dict in ui_components.items():
            GradioHelpers.set_components_elem_id_and_classes(
                provider_config_components=component_dict,
                provider_name=name,
                service_name=DatabaseService.CLASS_NAME,
            )
        save_button.click(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
            ),
            inputs=set(ui_components["pinecone_database"].values()),
        )
