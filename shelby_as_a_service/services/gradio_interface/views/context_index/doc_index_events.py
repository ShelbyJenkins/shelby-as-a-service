import time
from typing import Any, Literal, Optional, Type, get_args

import context_index.doc_index as doc_index_models
import gradio as gr
from context_index.doc_index.doc_index import DocIndex
from context_index.doc_index.doc_ingest import DocIngest
from gradio.components import Component
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService
from services.gradio_interface.gradio_base import GradioBase
from services.text_processing.ingest_processing.ingest_processing_service import (
    IngestProcessingService,
)


def builder_event_handlers(
    uic: dict[str, Any],
):
    domains_event_handlers(
        uic=uic,
        domains_dd=uic["cbc"]["domains_dd"],
        domain_tab_dict=uic["cbc"]["domain_tab_dict"],
        sources_dd=uic["cbc"]["sources_dd"],
    )
    sources_event_handlers(
        uic=uic, sources_dd=uic["cbc"]["sources_dd"], source_tab_dict=uic["cbc"]["source_tab_dict"]
    )

    domain_or_source_event_handlers(
        uic=uic,
        domain_or_source=doc_index_models.DomainModel,
        tab_dict=uic["cbc"]["domain_tab_dict"],
        dd=uic["cbc"]["domains_dd"],
    )
    domain_or_source_event_handlers(
        uic=uic,
        domain_or_source=doc_index_models.SourceModel,
        tab_dict=uic["cbc"]["source_tab_dict"],
        dd=uic["cbc"]["sources_dd"],
    )


def domains_event_handlers(
    uic: dict[str, Any],
    domains_dd: gr.Dropdown,
    domain_tab_dict: dict[str, Any],
    sources_dd: gr.Dropdown,
):
    domains_dd.change(
        fn=lambda *x: save_provider_settings(
            provider_config_components_values=x,
            domain_or_source=doc_index_models.DomainModel,
        ),
        inputs=set(
            GradioBase.list_provider_config_components(domain_tab_dict["services_components"])
        ),
    ).success(
        fn=lambda *x: save_domain_or_source_config_settings(
            domain_or_source_config_values=x,
            parent_domain=GradioBase.doc_index.domain,
        ),
        inputs=set(domain_tab_dict["domain_or_source_config"].values()),
    ).success(
        fn=lambda x: domain_or_source_update_config_components(
            domain_or_source=doc_index_models.DomainModel,
            set_instance_name=x,
        ),
        inputs=domains_dd,
        outputs=list(domain_tab_dict["domain_or_source_config"].values()),
    ).success(
        fn=lambda: update_services_and_providers(parent_instance=GradioBase.doc_index.domain),
        outputs=GradioBase.list_provider_config_components(domain_tab_dict["services_components"]),
    ).success(
        fn=lambda: update_domain_or_source_dd(doc_index_models.SourceModel),
        outputs=[sources_dd],
    )

    buttons: dict[str, gr.Button] = domain_tab_dict["buttons"]
    chat_tab_out_text: gr.Textbox = uic["primary_ui"]["chat_tab_out_text"]
    ingest_button: gr.Button = buttons["ingest_button"]
    ingest_button.click(
        api_name="ingest_button",
        fn=GradioBase.get_logs_and_send_to_interface,
        outputs=[chat_tab_out_text],
        trigger_mode="once",
    )

    ingest_button.click(
        api_name="doc_ingest",
        fn=lambda: (
            time.sleep(0.5),
            DocIngest.ingest_docs_from_doc_index_domains(
                domains=GradioBase.doc_index.domain,
            ),
        )[1],
    )

    clear_button: gr.Button = buttons["clear_domain_or_source"]
    clear_button.click(
        api_name="clear_domain_or_source",
        fn=GradioBase.get_logs_and_send_to_interface,
        outputs=[chat_tab_out_text],
        trigger_mode="once",
    )

    clear_button.click(
        api_name="clear_domain_or_source",
        fn=lambda: (
            time.sleep(0.5),
            GradioBase.doc_index.clear_domain(
                domain=GradioBase.doc_index.domain,
            ),
        )[1],
    )


def sources_event_handlers(
    uic: dict[str, Any],
    sources_dd: gr.Dropdown,
    source_tab_dict: dict[str, Any],
):
    sources_dd.change(
        fn=lambda *x: save_provider_settings(
            provider_config_components_values=x,
            domain_or_source=doc_index_models.SourceModel,
        ),
        inputs=set(
            GradioBase.list_provider_config_components(source_tab_dict["services_components"])
        ),
    ).success(
        fn=lambda *x: save_domain_or_source_config_settings(
            domain_or_source_config_values=x,
            parent_source=GradioBase.doc_index.source,
        ),
        inputs=set(source_tab_dict["domain_or_source_config"].values()),
    ).success(
        fn=lambda x: domain_or_source_update_config_components(
            domain_or_source=doc_index_models.SourceModel,
            set_instance_name=x,
        ),
        inputs=sources_dd,
        outputs=list(source_tab_dict["domain_or_source_config"].values()),
    ).success(
        fn=lambda: update_services_and_providers(parent_instance=GradioBase.doc_index.source),
        outputs=GradioBase.list_provider_config_components(source_tab_dict["services_components"]),
    )

    buttons: dict[str, gr.Button] = source_tab_dict["buttons"]
    chat_tab_out_text: gr.Textbox = uic["primary_ui"]["chat_tab_out_text"]
    ingest_button: gr.Button = buttons["ingest_button"]
    ingest_button.click(
        api_name="ingest_button",
        fn=GradioBase.get_logs_and_send_to_interface,
        outputs=[chat_tab_out_text],
        trigger_mode="once",
    )

    ingest_button.click(
        api_name="doc_ingest",
        fn=lambda: (
            time.sleep(0.5),
            DocIngest.ingest_docs_from_doc_index_sources(
                sources=GradioBase.doc_index.source,
            ),
        )[1],
    )
    clear_button: gr.Button = buttons["clear_domain_or_source"]
    clear_button.click(
        api_name="clear_domain_or_source",
        fn=GradioBase.get_logs_and_send_to_interface,
        outputs=[chat_tab_out_text],
        trigger_mode="once",
    )

    clear_button.click(
        api_name="clear_domain_or_source",
        fn=lambda: (
            time.sleep(0.5),
            GradioBase.doc_index.clear_source(
                source=GradioBase.doc_index.source,
            ),
        )[1],
    )


def domain_or_source_event_handlers(
    uic: dict[str, Any],
    domain_or_source: Type[doc_index_models.DomainModel] | Type[doc_index_models.SourceModel],
    tab_dict: dict[str, Any],
    dd: gr.Dropdown,
):
    buttons: dict[str, gr.Button] = tab_dict["buttons"]

    if domain_or_source is doc_index_models.DomainModel:
        domain = GradioBase.doc_index.domain
        source = None
    elif domain_or_source is doc_index_models.SourceModel:
        domain = GradioBase.doc_index.domain
        source = GradioBase.doc_index.source
    else:
        raise ValueError(
            f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
        )

    provider_dropdowns: dict[str, gr.Dropdown] = tab_dict["dropdowns"]
    service_provider_dropdown_select_events(
        domain_or_source=domain_or_source,
        dropdowns=provider_dropdowns,
    )

    make_new_button: gr.Button = buttons["make_new_button"]
    make_new_button.click(
        fn=lambda *x: create_new_domain_or_source(
            domain_or_source=domain_or_source,
            input_components=tab_dict["input_components"],
            component_values=x,
        ),
        inputs=list(tab_dict["input_components"].values()),
    ).success(
        fn=lambda: update_domain_or_source_dd(domain_or_source),
        outputs=[dd],
    )

    save_changes_button: gr.Button = buttons["save_changes_button"]
    save_changes_button.click(
        fn=lambda *x: save_provider_settings(
            provider_config_components_values=x,
            domain_or_source=domain_or_source,
        ),
        inputs=set(GradioBase.list_provider_config_components(tab_dict["services_components"])),
    ).success(
        fn=lambda *x: save_domain_or_source_config_settings(
            domain_or_source_config_values=x,
            parent_domain=domain,
            parent_source=source,
        ),
        inputs=set(tab_dict["domain_or_source_config"].values()),
    )


def save_domain_or_source_config_settings(
    domain_or_source_config_values,
    parent_domain: Optional[doc_index_models.DomainModel] = None,
    parent_source: Optional[doc_index_models.SourceModel] = None,
):
    if not parent_domain and not parent_source:
        raise ValueError("parent_domain and parent_source cannot both be not None")
    elif isinstance(parent_source, doc_index_models.SourceModel):
        parent_instance = parent_source
    elif isinstance(parent_domain, doc_index_models.DomainModel):
        parent_instance = parent_domain
    else:
        raise ValueError("parent_domain and parent_source must be SourceModel or DomainModel")

    for component, component_value in domain_or_source_config_values[0].items():
        if hasattr(parent_instance, component.elem_id):
            setattr(parent_instance, component.elem_id, component_value)
    DocIndex.commit_session
    gr.Info(f"Saved Changes to {parent_instance.name}")


def update_domain_or_source_dd(
    domain_or_source: Type[doc_index_models.DomainModel] | Type[doc_index_models.SourceModel],
):
    if domain_or_source is doc_index_models.DomainModel:
        return gr.update(
            value=GradioBase.doc_index.domain.name,
            choices=GradioBase.doc_index.domain_names,
        )
    elif domain_or_source is doc_index_models.SourceModel:
        return gr.update(
            value=GradioBase.doc_index.source.name,
            choices=GradioBase.doc_index.domain.source_names,
        )
    else:
        raise ValueError(
            f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
        )


def service_provider_dropdown_select_events(
    domain_or_source: Type[doc_index_models.DomainModel] | Type[doc_index_models.SourceModel],
    dropdowns: dict,
):
    def select_enabled_provider_event(
        provider_select_dd: gr.Dropdown,
        doc_index_model_name: doc_index_models.DOC_INDEX_MODEL_NAMES,
    ):
        provider_select_dd.input(
            fn=lambda x: GradioBase.doc_index.set_current_domain_or_source_provider_instance(
                domain_or_source=domain_or_source,
                doc_index_model_name=doc_index_model_name,
                set_name=x,
            ),
            inputs=provider_select_dd,
        )

    select_enabled_provider_event(
        dropdowns["doc_loaders_dd"], doc_index_models.DocLoaderModel.CLASS_NAME  # type: ignore
    )
    select_enabled_provider_event(
        dropdowns["doc_ingest_proc_dd"], doc_index_models.DocIngestProcessorModel.CLASS_NAME  # type: ignore
    )
    select_enabled_provider_event(
        dropdowns["doc_dbs_dd"], doc_index_models.DocDBModel.CLASS_NAME  # type: ignore
    )


def domain_or_source_update_config_components(
    domain_or_source: Type[doc_index_models.DomainModel] | Type[doc_index_models.SourceModel],
    set_instance_name: str,
) -> list:
    output = []
    parent_instance: doc_index_models.DomainModel | doc_index_models.SourceModel
    if domain_or_source is doc_index_models.DomainModel:
        parent_instance = GradioBase.doc_index.get_index_model_instance(
            list_of_instances=GradioBase.doc_index.index.domains,
            name=set_instance_name,
        )
        GradioBase.doc_index.index.current_domain = parent_instance
    elif domain_or_source is doc_index_models.SourceModel:
        parent_instance = GradioBase.doc_index.get_index_model_instance(
            name=set_instance_name,
            list_of_instances=GradioBase.doc_index.domain.sources,
        )
        GradioBase.doc_index.domain.current_source = parent_instance
        DocIndex.session.flush()

    else:
        raise ValueError(
            f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
        )

    output.append(gr.Textbox(placeholder=parent_instance.name))
    output.append(gr.Textbox(placeholder=parent_instance.description))
    if isinstance(parent_instance, doc_index_models.SourceModel):
        output.append(gr.Textbox(value=parent_instance.source_uri))
    output.append(gr.Checkbox(value=parent_instance.batch_update_enabled))

    return output


def update_services_and_providers(
    parent_instance: doc_index_models.DomainModel | doc_index_models.SourceModel,
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

    return GradioBase.list_provider_config_components(services_components)


def save_provider_settings(
    provider_config_components_values,
    domain_or_source: Type[doc_index_models.DomainModel] | Type[doc_index_models.SourceModel],
):
    if domain_or_source is doc_index_models.DomainModel:
        parent_domain_or_source = GradioBase.doc_index.domain
    elif domain_or_source is doc_index_models.SourceModel:
        parent_domain_or_source = GradioBase.doc_index.source
    else:
        raise ValueError(
            f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
        )
    provider_name = None
    provider_model = None
    for component, component_value in provider_config_components_values[0].items():
        if component.elem_classes[1] != provider_name:
            service_name = component.elem_classes[0]
            provider_name = component.elem_classes[1]
            provider_model = GradioBase.doc_index.get_provider_instance_model_from_service_name(
                service_name=service_name,
                provider_name=provider_name,
                parent_domain_or_source=parent_domain_or_source,
            )
            if not hasattr(provider_model, "config"):
                raise ValueError(f"provider_model {provider_model} has no config attribute")
        if (
            provider_model is not None
            and provider_model.config.get(component.elem_id, None) is not None
        ):
            provider_model.config[component.elem_id] = component_value

    DocIndex.commit_session


def create_new_domain_or_source(
    domain_or_source: Type[doc_index_models.DomainModel] | Type[doc_index_models.SourceModel],
    input_components: dict[str, Component],
    component_values,
):
    if domain_or_source is doc_index_models.DomainModel:
        create = GradioBase.doc_index.create_domain_or_source
        clone_name = GradioBase.doc_index.domain.name
        set_current = lambda instance: setattr(
            GradioBase.doc_index.index, "current_domain", instance
        )
    elif domain_or_source is doc_index_models.SourceModel:
        create = lambda **kwargs: GradioBase.doc_index.create_domain_or_source(
            parent_domain=GradioBase.doc_index.domain, **kwargs
        )
        clone_name = GradioBase.doc_index.source.name
        set_current = lambda instance: setattr(
            GradioBase.doc_index.domain, "current_source", instance
        )
    else:
        raise ValueError(
            f"domain_or_source must be doc_index_models.DomainModel or doc_index_models.SourceModel"
        )

    ui_state = {k: v for k, v in zip(input_components.keys(), component_values)}

    from_template = ui_state.get("make_new_from_template_checkbox", False)
    from_clone = ui_state.get("make_new_from_clone_checkbox", False)
    if from_template and from_clone:
        gr.Warning("Cannot use both template and clone to create new domain. Defaulting to clone.")

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
