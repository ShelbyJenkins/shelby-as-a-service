from typing import Any, Literal, Optional, Type, get_args

import context_index.doc_index as doc_index_models
import gradio as gr
from context_index.doc_index.doc_index import DocIndex
from context_index.doc_index.doc_ingest import DocIngest
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
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6

    domain_tab_dict: dict[str, Any]
    source_tab_dict: dict[str, Any]
    domains_dd: gr.Dropdown
    sources_dd: gr.Dropdown

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

        self.uic: dict[str, Any] = {}  # ui components

    def create_primary_ui(self):
        with gr.Column(elem_classes="primary_ui_col"):
            self.uic["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {DocIndexView.CLASS_UI_NAME}",
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
                # ui_components = DatabaseService.create_service_management_settings_ui()
                # self.create_management_tab_event_handlers(ui_components, save_button)

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
            value=self.doc_index.domain.source.object_model.enabled_doc_ingest_template.ingest_template_name,
            choices=self.doc_index.domain.source.list_of_ingest_template_names,
            label="Ingest Preset",
            allow_custom_value=False,
        )

        with gr.Row():
            self.uic["domains_dropdown"] = gr.Dropdown(
                value=self.doc_index.domain.object_model.name,
                choices=self.doc_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
            )
            self.uic["sources_dropdown"] = gr.Dropdown(
                value=self.doc_index.domain.source.object_model.name,
                choices=self.doc_index.domain.source_names,
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
                value=self.doc_index.domain.name,
                choices=self.doc_index.domain_names,
                label="Current Domain",
                allow_custom_value=False,
                multiselect=False,
            )
            self.sources_dd = gr.Dropdown(
                value=self.doc_index.source.name,
                choices=self.doc_index.domain.source_names,
                label="Current Source",
                allow_custom_value=False,
                multiselect=False,
            )

        with gr.Tab(label="Docs"):
            pass
        with gr.Tab(label="Sources"):
            self.source_tab_dict = self.create_builder_domain_or_source_tab(
                domain_or_source=doc_index_models.SourceModel
            )
            self.create_service_provider_select_events(
                domain_or_source=doc_index_models.SourceModel,
                dropdowns=self.source_tab_dict["dropdowns"],
            )
        with gr.Tab(label="Topics"):
            self.domain_tab_dict = self.create_builder_domain_or_source_tab(
                domain_or_source=doc_index_models.DomainModel
            )
            self.create_service_provider_select_events(
                domain_or_source=doc_index_models.DomainModel,
                dropdowns=self.domain_tab_dict["dropdowns"],
            )
        with gr.Tab(label="Batch Update Index"):
            gr.Button(
                value="Run Full Index Ingest Pipeline",
                variant="primary",
            )

        self.create_builder_event_handlers()

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
            buttons["test_loader_button"] = gr.Button(
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

    def update_services_and_providers(
        self, parent_instance: doc_index_models.DomainModel | doc_index_models.SourceModel
    ):
        services_components = {}
        (
            _,
            doc_loader_components_dict,
        ) = DocLoadingService.create_doc_index_ui_components(
            parent_instance=parent_instance,
            groups_rendered=True,
        )
        services_components["doc_loaders"] = doc_loader_components_dict
        (
            _,
            doc_ingest_processor_components_dict,
        ) = IngestProcessingService.create_doc_index_ui_components(
            parent_instance=parent_instance,
            groups_rendered=True,
        )
        services_components["doc_ingest_procs"] = doc_ingest_processor_components_dict
        (
            _,
            doc_dbs_components_dict,
        ) = DatabaseService.create_doc_index_ui_components(
            parent_instance=parent_instance,
            groups_rendered=True,
        )
        services_components["doc_dbs"] = doc_dbs_components_dict

        return self.list_provider_config_components(services_components)

    def create_builder_event_handlers(self):
        def update_domain_or_source_tab_config_components(
            domain_or_source: Type[doc_index_models.DomainModel]
            | Type[doc_index_models.SourceModel],
            set_instance_name: str,
        ) -> list:
            output = []

            if domain_or_source is doc_index_models.DomainModel:
                parent_instance = self.doc_index.get_index_model_instance(
                    list_of_instances=self.doc_index.index.domains,
                    name=set_instance_name,
                )
                self.doc_index.index.current_domain = parent_instance
            elif domain_or_source is doc_index_models.SourceModel:
                parent_instance = self.doc_index.get_index_model_instance(
                    name=set_instance_name,
                    list_of_instances=self.doc_index.domain.sources,
                )
                self.doc_index.domain.current_source = parent_instance
                DocIndex.session.flush()

            else:
                raise ValueError(
                    f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
                )

            output.append(gr.Textbox(placeholder=parent_instance.name))
            output.append(gr.Textbox(placeholder=parent_instance.description))
            if domain_or_source is doc_index_models.SourceModel:
                output.append(gr.Textbox(value=parent_instance.source_uri))
            output.append(gr.Checkbox(value=parent_instance.batch_update_enabled))

            return output

        self.domains_dd.change(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
                domain_or_source=self.doc_index.domain,
            ),
            inputs=set(
                self.list_provider_config_components(self.domain_tab_dict["services_components"])
            ),
        ).success(
            fn=lambda *x: save_domain_or_source_config_settings(
                domain_or_source_config_values=x,
                parent_domain=self.doc_index.domain,
            ),
            inputs=set(self.domain_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda x: update_domain_or_source_tab_config_components(
                domain_or_source=doc_index_models.DomainModel,
                set_instance_name=x,
            ),
            inputs=self.domains_dd,
            outputs=list(self.domain_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda: self.update_services_and_providers(parent_instance=self.doc_index.domain),
            outputs=self.list_provider_config_components(
                self.domain_tab_dict["services_components"]
            ),
        ).success(
            fn=lambda: update_domain_or_source_dd(doc_index_models.SourceModel),
            outputs=[self.sources_dd],
        )

        self.sources_dd.change(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
                domain_or_source=self.doc_index.source,
            ),
            inputs=set(
                self.list_provider_config_components(self.source_tab_dict["services_components"])
            ),
        ).success(
            fn=lambda *x: save_domain_or_source_config_settings(
                domain_or_source_config_values=x,
                parent_source=self.doc_index.source,
            ),
            inputs=set(self.source_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda x: update_domain_or_source_tab_config_components(
                domain_or_source=doc_index_models.SourceModel,
                set_instance_name=x,
            ),
            inputs=self.sources_dd,
            outputs=list(self.source_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda: self.update_services_and_providers(parent_instance=self.doc_index.source),
            outputs=self.list_provider_config_components(
                self.source_tab_dict["services_components"]
            ),
        )

        self.domain_tab_dict["buttons"]["make_new_button"].click(
            fn=lambda *x: create_new_domain_or_source(
                domain_or_source=doc_index_models.DomainModel,
                input_components=self.domain_tab_dict["input_components"],
                component_values=x,
            ),
            inputs=list(self.domain_tab_dict["input_components"].values()),
        ).success(
            fn=lambda: update_domain_or_source_dd(doc_index_models.DomainModel),
            outputs=[self.domains_dd],
        )

        self.source_tab_dict["buttons"]["make_new_button"].click(
            fn=lambda *x: create_new_domain_or_source(
                domain_or_source=doc_index_models.SourceModel,
                input_components=self.source_tab_dict["input_components"],
                component_values=x,
            ),
            inputs=list(self.source_tab_dict["input_components"].values()),
        ).success(
            fn=lambda: update_domain_or_source_dd(doc_index_models.SourceModel),
            outputs=[self.sources_dd],
        )

        self.domain_tab_dict["buttons"]["save_changes_button"].click(
            fn=lambda *x: save_domain_or_source_config_settings(
                domain_or_source_config_values=x,
                parent_domain=self.doc_index.domain,
            ),
            inputs=set(self.domain_tab_dict["domain_or_source_config"].values()),
        ).success(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
                domain_or_source=self.doc_index.domain,
            ),
            inputs=set(
                self.list_provider_config_components(self.domain_tab_dict["services_components"])
            ),
        )

        self.source_tab_dict["buttons"]["save_changes_button"].click(
            fn=lambda *x: self.save_provider_settings(
                provider_config_components_values=x,
                domain_or_source=self.doc_index.source,
            ),
            inputs=set(
                self.list_provider_config_components(self.source_tab_dict["services_components"])
            ),
        ).success(
            fn=lambda *x: save_domain_or_source_config_settings(
                domain_or_source_config_values=x,
                parent_source=self.doc_index.source,
            ),
            inputs=set(self.source_tab_dict["domain_or_source_config"].values()),
        )

        self.domain_tab_dict["buttons"]["ingest_button"].click(
            fn=lambda: DocIngest.ingest_docs_from_context_index_source_or_domain(
                domain=self.doc_index.domain,
            )
        )
        self.source_tab_dict["buttons"]["ingest_button"].click(
            fn=lambda: DocIngest.ingest_docs_from_context_index_source_or_domain(
                source=self.doc_index.source,
            )
        )

        def create_new_domain_or_source(
            domain_or_source: Type[doc_index_models.DomainModel]
            | Type[doc_index_models.SourceModel],
            input_components,
            component_values,
        ):
            if domain_or_source is doc_index_models.DomainModel:
                create = self.doc_index.create_domain_or_source
                clone_name = self.doc_index.domain.name
                set_current = lambda instance: setattr(
                    self.doc_index.index, "current_domain", instance
                )
            elif domain_or_source is doc_index_models.SourceModel:
                create = lambda **kwargs: self.doc_index.create_domain_or_source(
                    parent_domain=self.doc_index.domain, **kwargs
                )
                clone_name = self.doc_index.source.name
                set_current = lambda instance: setattr(
                    self.doc_index.domain, "current_source", instance
                )
            else:
                raise ValueError(
                    f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
                )

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
            DocIndex.commit_context_index()

        def save_domain_or_source_config_settings(
            domain_or_source_config_values,
            parent_domain: Optional[doc_index_models.DomainModel] = None,
            parent_source: Optional[doc_index_models.SourceModel] = None,
        ):
            if parent_domain and parent_source:
                raise ValueError("parent_domain and parent_source cannot both be not None")
            parent_instance = parent_domain or parent_source
            for component, component_value in domain_or_source_config_values[0].items():
                if hasattr(parent_instance, component.elem_id):
                    setattr(parent_instance, component.elem_id, component_value)
            DocIndex.commit_context_index()
            gr.Info(f"Saved Changes to {self.doc_index.source.name}")

        def update_domain_or_source_dd(
            domain_or_source: Type[doc_index_models.DomainModel]
            | Type[doc_index_models.SourceModel],
        ):
            if domain_or_source is doc_index_models.DomainModel:
                return gr.update(
                    value=self.doc_index.domain.name,
                    choices=self.doc_index.domain_names,
                )
            elif domain_or_source is doc_index_models.SourceModel:
                return gr.update(
                    value=self.doc_index.source.name,
                    choices=self.doc_index.domain.source_names,
                )
            else:
                raise ValueError(
                    f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
                )

    def create_service_provider_select_events(
        self,
        domain_or_source: Type[doc_index_models.DomainModel] | Type[doc_index_models.SourceModel],
        dropdowns: dict,
    ):
        def select_enabled_provider_event(
            provider_select_dd: gr.Dropdown,
            doc_index_model_name: doc_index_models.DOC_INDEX_MODEL_NAMES,
        ):
            provider_select_dd.input(
                fn=lambda x: self.doc_index.set_current_domain_or_source_provider_instance(
                    domain_or_source=domain_or_source,
                    doc_index_model_name=doc_index_model_name,
                    set_name=x,
                ),
                inputs=provider_select_dd,
            )

        select_enabled_provider_event(
            dropdowns["doc_loaders_dd"], doc_index_models.DocLoaderModel.CLASS_NAME
        )
        select_enabled_provider_event(
            dropdowns["doc_ingest_proc_dd"], doc_index_models.DocIngestProcessorModel.CLASS_NAME
        )
        select_enabled_provider_event(
            dropdowns["doc_dbs_dd"], doc_index_models.DocDBModel.CLASS_NAME
        )

    def save_provider_settings(
        self,
        provider_config_components_values,
        domain_or_source: Optional[
            doc_index_models.DomainModel | doc_index_models.SourceModel
        ] = None,
    ):
        if isinstance(domain_or_source, doc_index_models.DomainModel):
            domain_or_source = self.doc_index.domain
        elif isinstance(domain_or_source, doc_index_models.SourceModel):
            domain_or_source = self.doc_index.source

        provider_name = None
        provider_model = None
        for component, component_value in provider_config_components_values[0].items():
            if component.elem_classes[1] != provider_name:
                service_name = component.elem_classes[0]
                provider_name = component.elem_classes[1]
                provider_model = self.doc_index.get_provider_instance_model_from_service_name(
                    service_name=service_name,
                    provider_name=provider_name,
                    domain_or_source=domain_or_source,
                )
                if not hasattr(provider_model, "config"):
                    raise ValueError(f"provider_model {provider_model} has no config attribute")
            if (
                provider_model is not None
                and provider_model.config.get(component.elem_id, None) is not None
            ):
                provider_model.config[component.elem_id] = component_value

        DocIndex.commit_context_index()

    def create_management_tab_event_handlers(self, ui_components, save_button):
        for name, component_dict in ui_components.items():
            self.set_components_elem_id_and_classes(
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
