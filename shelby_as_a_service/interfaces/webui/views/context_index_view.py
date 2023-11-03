import typing
from typing import Any, Dict, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.context_index.context_index import ContextConfig, ContextIndex, DocDB, DocLoading
from services.context_index.context_index_model import (
    ContextConfigModel,
    ContextIndexModel,
    DocDBModel,
    DomainModel,
    SourceModel,
)
from services.context_index.ingest import DocIngest
from services.database.database_service import DataBaseService
from services.document_loading.document_loading_service import DocLoadingService


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
    doc_loader_service: DocLoadingService
    context_index: ContextIndex
    # current_domain: DataDomain
    # current_source: DataSource
    uic: dict[str, Any]
    domains_dd: gr.Dropdown
    sources_dd: gr.Dropdown

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

        self.doc_loader_service = DocLoadingService()
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
                value=self.context_index.domain.object_model.name,
                choices=self.context_index.list_of_domain_names,
                label="Current Topic",
                allow_custom_value=False,
                multiselect=False,
            )
            self.sources_dd = gr.Dropdown(
                value=self.context_index.domain.source.object_model.name,
                choices=self.context_index.domain.list_of_source_names,
                label="Current Source",
                allow_custom_value=False,
                multiselect=False,
            )

        with gr.Tab(label="Docs"):
            pass
        with gr.Tab(label="Sources"):
            self.create_builder_sources_tab()
        with gr.Tab(label="Topics"):
            self.create_builder_topic_tab()
        with gr.Tab(label="Batch Update Index"):
            gr.Button(
                value="Run Full Index Ingest Pipeline",
                variant="primary",
            )

        self.create_builder_event_handlers()

    def create_builder_topic_tab(self):
        input_components = {}
        model_config_components = {}
        buttons = {}
        services_components = {}

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
                input_components["make_new_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.object_model.DEFAULT_DOMAIN_NAME,
                    lines=1,
                    container=True,
                    label="New Domain Name",
                )
                input_components["make_new_description"] = gr.Textbox(
                    placeholder=self.context_index.domain.object_model.DEFAULT_DOMAIN_DESCRIPTION,
                    lines=1,
                    container=True,
                    label="New Domain Description",
                )
                with gr.Row():
                    input_components["make_new_from_template_dropdown"] = gr.Dropdown(
                        value=self.context_index.domain.object_model.DEFAULT_TEMPLATE_NAME,
                        choices=self.context_index.list_of_context_template_names,
                        label="Use Template",
                        allow_custom_value=False,
                    )
                    input_components["make_new_from_template_checkbox"] = gr.Checkbox(
                        value=False,
                        label="Use Selected Template",
                    )
                    input_components["make_new_from_clone_checkbox"] = gr.Checkbox(
                        value=False,
                        label="Clone Current Domain",
                    )

            with gr.Accordion(label="Config Templates", open=False):
                input_components["load_template_dropdown"] = gr.Dropdown(
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

                input_components["new_template_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.object_model.name,
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
                input_components["update_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.object_model.name,
                    lines=1,
                    container=True,
                    label="New Topic Name",
                )
                input_components["update_description"] = gr.Textbox(
                    placeholder=self.context_index.domain.object_model.description,
                    lines=1,
                    container=True,
                    label="New Topic Description",
                )
                input_components["delete_textbox"] = gr.Textbox(
                    placeholder="Type Topic Name to confirm deletion.",
                    lines=1,
                    show_label=False,
                )
                buttons["delete_button"] = gr.Button(
                    value="Delete Topic and all it's configs and documents.",
                    min_width=0,
                    size="sm",
                    variant="stop",
                )
        with gr.Tab(label="Loader"):
            pass
            doc_loader_ui_components_dict = self.doc_loader_service.create_service_ui_components(
                context_config=self.context_index.domain.object_model.context_config,
                groups_rendered=False,
            )
            services_components["doc_loaders"] = doc_loader_ui_components_dict
        with gr.Tab(label="Processor"):
            gr.Textbox(
                value="Not Implemented",
                show_label=False,
                lines=1,
            )
            # self.doc_ingest.create_processor_ui()

        with gr.Tab(label="Database"):
            input_components["database_provider"] = gr.Dropdown(
                value=self.context_index.domain.object_model.context_config.doc_db.provider_name,
                choices=self.context_index.list_of_provider_names,
                show_label=False,
                info="Default document database for the topic. Database context_config are managed elsewhere.",
            )
        with gr.Tab(label="Ingest Topic"):
            input_components["batch_update_enabled"] = gr.Checkbox(
                value=self.context_index.domain.object_model.context_config.batch_update_enabled,
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

        domains = {}
        domains["input_components"] = input_components
        domains["services_components"] = services_components
        domains["model_config_components"] = model_config_components
        domains["buttons"] = buttons
        self.uic["cbc"]["domains"] = domains

    def create_builder_sources_tab(self):
        input_components = {}
        buttons = {}
        model_config_components = {}
        services_components = {}

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
                input_components["make_new_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.object_model.DEFAULT_SOURCE_NAME,
                    lines=1,
                    container=True,
                    label="New Source Name",
                )
                input_components["make_new_description"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.object_model.DEFAULT_SOURCE_DESCRIPTION,
                    lines=1,
                    container=True,
                    label="New Source Description",
                )
                with gr.Row():
                    input_components["make_new_from_template_dropdown"] = gr.Dropdown(
                        value=self.context_index.domain.source.object_model.DEFAULT_TEMPLATE_NAME,
                        choices=self.context_index.list_of_context_template_names,
                        label="Use Template",
                        allow_custom_value=False,
                    )
                    input_components["make_new_from_template_checkbox"] = gr.Checkbox(
                        value=False,
                        label="Use Selected Template",
                    )

                    input_components["make_new_from_clone_checkbox"] = gr.Checkbox(
                        value=False,
                        label="Clone Current Source",
                    )

            with gr.Accordion(label="Config Templates", open=False):
                input_components["load_template_dropdown"] = gr.Dropdown(
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

                input_components["new_template_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.object_model.name,
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
                input_components["update_name"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.object_model.name,
                    lines=1,
                    container=True,
                    label="New Source Name",
                )
                input_components["update_description"] = gr.Textbox(
                    placeholder=self.context_index.domain.source.object_model.description,
                    lines=1,
                    container=True,
                    label="New Source Description",
                )
                input_components["delete_textbox"] = gr.Textbox(
                    placeholder="Type Source Name to confirm deletion.",
                    lines=1,
                    show_label=False,
                )
                buttons["delete_button"] = gr.Button(
                    value="Delete Source and all it's configs and documents.",
                    min_width=0,
                    size="sm",
                    variant="stop",
                )

        with gr.Tab(label="Loader"):
            # model_config_components["url_textbox"] = gr.Textbox(
            #     placeholder="Web URL or Local Filepath",
            #     lines=1,
            #     show_label=False,
            # )
            doc_loader_ui_components_dict = self.doc_loader_service.create_service_ui_components(
                context_config=self.context_index.domain.source.object_model.context_config,
                groups_rendered=False,
            )
            services_components["doc_loaders"] = doc_loader_ui_components_dict

        with gr.Tab(label="Processor"):
            gr.Textbox(
                value="Not Implemented",
                show_label=False,
                lines=1,
            )
            # self.doc_ingest.create_processor_ui()

        with gr.Tab(label="Database"):
            # model_config_components["database_dropdown"] = gr.Dropdown(
            #     value=self.context_index.domain.source.object_model.context_config.doc_db.provider_name,
            #     choices=self.context_index.list_of_provider_names,
            #     show_label=False,
            #     info="Default document database for the Source. Database context_config are managed elsewhere.",
            # )
            pass
        with gr.Tab(label="Ingest Source"):
            model_config_components["batch_update_enabled"] = gr.Checkbox(
                value=self.context_index.domain.source.object_model.context_config.batch_update_enabled,
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
        sources["input_components"] = input_components
        sources["services_components"] = services_components
        sources["model_config_components"] = model_config_components
        sources["buttons"] = buttons
        self.uic["cbc"]["sources"] = sources

    def listify_dict(self, dict):
        output = []
        for service_name, service in dict.items():
            for component in service["ui_components_list"]:
                output.append(component)
        return output

    def update_services_and_providers(self, context_config):
        output = []
        doc_loader_ui_components_dict = self.doc_loader_service.create_service_ui_components(
            context_config=context_config
        )
        output.extend(doc_loader_ui_components_dict["ui_components_list"])

        return output

    def create_builder_event_handlers(self):
        domains = self.uic["cbc"]["domains"]
        sources = self.uic["cbc"]["sources"]

        def update_domain_tab_ui_components(new_domain_name) -> list:
            output = []
            self.context_index.set_domain(domain_name=new_domain_name)
            output.append(gr.Textbox(placeholder=self.context_index.domain.object_model.name))
            output.append(
                gr.Textbox(placeholder=self.context_index.domain.object_model.description)
            )
            output.append(
                gr.Checkbox(
                    value=self.context_index.domain.object_model.context_config.batch_update_enabled
                )
            )

            return output

        def create_new_domain(input_components, component_values):
            ui_state = {k: v for k, v in zip(input_components.keys(), component_values)}

            from_template = ui_state.get("make_new_from_template_checkbox", False)
            from_clone = ui_state.get("make_new_from_clone_checkbox", False)
            if from_template and from_clone:
                gr.Warning(
                    "Cannot use both template and clone to create new domain. Defaulting to clone."
                )

            if from_clone:
                new_domain_name, _ = self.context_index.clone_domain(
                    new_domain_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                    clone_domain_name=self.context_index.domain.object_model.name,
                )
            elif from_template:
                new_domain_name, _ = self.context_index.domain.create_domain(
                    new_domain_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                    requested_template_name=ui_state.get("make_new_from_template_dropdown", None),
                )
            else:
                new_domain_name, _ = self.context_index.domain.create_domain(
                    new_domain_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                )
            self.context_index.set_domain(domain_name=new_domain_name)

        def update_source_tab_ui_components(new_source_name) -> list:
            self.context_index.domain.set_source(source_name=new_source_name)
            output = []
            output.append(
                gr.Textbox(placeholder=self.context_index.domain.source.object_model.name)
            )
            output.append(
                gr.Textbox(placeholder=self.context_index.domain.source.object_model.description)
            )
            output.append(
                gr.Checkbox(
                    value=self.context_index.domain.source.object_model.context_config.batch_update_enabled
                )
            )
            return output

        def create_new_source(input_components, component_values):
            ui_state = {k: v for k, v in zip(input_components.keys(), component_values)}

            from_template = ui_state.get("make_new_from_template_checkbox", False)
            from_clone = ui_state.get("make_new_from_clone_checkbox", False)
            if from_template and from_clone:
                gr.Warning(
                    "Cannot use both template and clone to create new source. Defaulting to clone."
                )

            if from_clone:
                new_source_name, _ = self.context_index.domain.clone_source(
                    new_source_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                    clone_source_name=self.context_index.domain.source.object_model.name,
                )
            elif from_template:
                new_source_name, _ = self.context_index.domain.create_source(
                    new_source_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                    requested_template_name=ui_state.get("make_new_from_template_dropdown", None),
                )
            else:
                new_source_name, _ = self.context_index.domain.create_source(
                    new_source_name=ui_state.get("make_new_name", None),
                    new_description=ui_state.get("make_new_description", None),
                )
            self.context_index.domain.set_source(source_name=new_source_name)

        domains["buttons"]["make_new_button"].click(
            fn=lambda *x: create_new_domain(domains["input_components"], x),
            inputs=list(domains["input_components"].values()),
        ).success(
            fn=lambda: gr.update(
                value=self.context_index.domain.object_model.name,
                choices=self.context_index.list_of_domain_names,
            ),
            outputs=self.domains_dd,
        )

        self.domains_dd.change(
            fn=lambda: save_settings(
                context_config=self.context_index.domain.object_model.context_config,
                config_dict_from_gradio=sources,
            )
        ).success(
            fn=lambda: gr.Info(f"Saved Changes to {self.context_index.domain.domain_name}")
        ).success(
            fn=lambda x: update_domain_tab_ui_components(x),
            inputs=self.domains_dd,
            outputs=list(sources["model_config_components"].values()),
        ).success(
            fn=lambda: self.update_services_and_providers(
                self.context_index.domain.object_model.context_config
            ),
            outputs=self.listify_dict(dict=domains["services_components"]),
        ).success(
            fn=lambda: gr.update(
                value=self.context_index.domain.source.object_model.name,
                choices=self.context_index.domain.list_of_source_names,
            ),
            outputs=self.sources_dd,
        )

        domains["buttons"]["save_changes_button"].click(
            fn=lambda: save_settings(
                context_config=self.context_index.domain.object_model.context_config,
                config_dict_from_gradio=domains,
            )
        ).success(fn=lambda: gr.Info(f"Saved Changes to {self.context_index.domain.domain_name}"))

        sources["buttons"]["make_new_button"].click(
            fn=lambda *x: create_new_source(sources["input_components"], x),
            inputs=list(sources["input_components"].values()),
        ).success(
            fn=lambda: gr.update(
                value=self.context_index.domain.source.object_model.name,
                choices=self.context_index.domain.list_of_source_names,
            ),
            outputs=self.sources_dd,
        )

        self.sources_dd.change(
            fn=lambda: save_settings(
                context_config=self.context_index.domain.source.object_model.context_config,
                config_dict_from_gradio=sources,
            )
        ).success(
            fn=lambda: gr.Info(f"Saved Changes to {self.context_index.domain.source.source_name}")
        ).success(
            fn=lambda x: update_source_tab_ui_components(x),
            inputs=self.sources_dd,
            outputs=list(sources["model_config_components"].values()),
        ).success(
            fn=lambda: self.update_services_and_providers(
                self.context_index.domain.source.object_model.context_config
            ),
            outputs=self.listify_dict(dict=sources["services_components"]),
        )

        sources["buttons"]["save_changes_button"].click(
            fn=lambda: save_settings(
                context_config=self.context_index.domain.source.object_model.context_config,
                config_dict_from_gradio=sources,
            )
        ).success(
            fn=lambda: gr.Info(f"Saved Changes to {self.context_index.domain.source.source_name}")
        )

        def save_settings(context_config: ContextConfigModel, config_dict_from_gradio):
            for key, component in config_dict_from_gradio["model_config_components"].items():
                if hasattr(context_config, key):
                    setattr(context_config, key, component.value)

            def build_provider_config_dict(components, provider_model):
                provider_config_dict = {}
                for key, component in components.items():
                    provider_config_dict[key] = component.value

                setattr(provider_model, "provider_config", provider_config_dict)

            if doc_loaders := config_dict_from_gradio["services_components"].get(
                "doc_loaders", None
            ):
                enabled_provider = doc_loaders.get("provider_select_dropdown", None)
                DocLoading.set_doc_loader(
                    context_config_or_template=context_config,
                    requested_doc_loader_name=enabled_provider.value,
                )
                ui_components_config_dict = doc_loaders.get("ui_components_config_dict", None)
                for name, components in ui_components_config_dict.items():
                    provider_model = DocLoading.get_doc_loader(
                        requested_doc_loader_name=name,
                        list_of_doc_loaders=doc_loaders,
                    )
                    build_provider_config_dict(components, provider_model)

            ContextIndex.commit_context_index()
