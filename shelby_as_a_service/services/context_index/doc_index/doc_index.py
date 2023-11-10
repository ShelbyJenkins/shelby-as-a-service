import logging
from typing import Any, Optional, Type, Union

from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from services.context_index.index_base import IndexBase
from services.text_processing.ingest_processing.ingest_processing_service import (
    IngestProcessingService,
)

from services.context_index.doc_index.doc_ingest import DocIngest
from 
from .doc_index_model import (
    DocDBModel,
    DocIndexModel,
    DocIndexTemplateModel,
    DocIngestProcessorModel,
    DocLoaderModel,
    DomainModel,
    SourceModel,
)


class DocIndex(IndexBase):
    doc_index_model: DocIndexModel
    session: Session
    log: logging.Logger
    object_model: Union[DomainModel, SourceModel]
    context_template: DocIndexTemplateModel

    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)

        DocIndex.setup_index()
        DocIndex.session = DocIndex.get_session()
        try:
            self.setup_context_index()
        except SQLAlchemyError:
            DocIndex.session.rollback()
            raise

    def setup_context_index(self):
        if doc_index_model := self.session.query(DocIndexModel).first():
            DocIndex.doc_index_model = doc_index_model
            self.add_doc_dbs_to_index()
            self.add_default_context_templates_to_index()
            # Need a function here to update any new services/providers to sources/domains
        else:
            DocIndex.doc_index_model = DocIndexModel()
            DocIndex.session.add(DocIndex.doc_index_model)
            DocIndex.session.flush()

            self.add_doc_dbs_to_index()
            self.add_default_context_templates_to_index()

            self.create_domain()

        DocIndex.commit_context_index()

    @staticmethod
    def commit_context_index():
        DocIndex.session = DocIndex.commit_session(DocIndex.session)
        DocIndex.session.add(DocIndex.doc_index_model)

    @property
    def list_of_all_context_index_domain_names(self) -> list:
        return [domain.name for domain in DocIndex.doc_index_model.domains]

    @property
    def index(self) -> "DocIndexModel":
        return DocIndex.doc_index_model

    @property
    def domain(self) -> "DomainModel":
        if getattr(self.index, "current_domain", None) is None:
            raise Exception(f"{self.index} has no domain.")
        return self.index.current_domain

    @property
    def source(self) -> "SourceModel":
        if getattr(self.domain, "current_source", None) is None:
            raise Exception(f"{self.domain} has no source.")
        return self.domain.current_source

    @property
    def list_of_all_context_index_source_names(self) -> list:
        all_sources = DocIndex.session.query(SourceModel).all()
        return [source.name for source in all_sources]

    def parse_parent_instance(
        self,
        parent_domain: Optional[DomainModel] = None,
        parent_source: Optional[SourceModel] = None,
    ) -> Union[DomainModel, SourceModel]:
        if parent_domain and parent_source:
            raise Exception(
                "Unexpected error: parent_domain and parent_source should not both be set."
            )
        if parent_domain:
            return parent_domain
        elif parent_source:
            return parent_source
        else:
            raise Exception("Unexpected error: parent_domain or parent_source should be set.")

    def get_or_create_doc_ingest_processor_instance(
        self,
        parent_domain: Optional[DomainModel] = None,
        parent_source: Optional[SourceModel] = None,
        id: Optional[int] = None,
        name: Optional[str] = None,
        config: dict[str, Any] = {},
    ) -> DocIngestProcessorModel:
        if parent_domain or parent_source:
            parent_instance = self.parse_parent_instance(
                parent_domain=parent_domain,
                parent_source=parent_source,
            )
            list_of_model_instances = parent_instance.doc_ingest_processors
            requested_instance = self.get_model_instance(
                list_of_model_instances=list_of_model_instances,
                id=id,
                name=name,
            )
        else:
            if not name:
                raise Exception("Unexpected error: name should not be None at this point.")
            provider_class_model = self.get_service_provider_class_model(
                list_of_service_providers=IngestProcessingService.REQUIRED_CLASSES,
                requested_provider_name=name,
            )
            requested_instance = DocIngestProcessorModel(
                name=name,
                config=provider_class_model.ClassConfigModel(**config).model_dump(),
            )
            DocIndex.session.flush()
        if not isinstance(requested_instance, DocIngestProcessorModel):
            raise Exception(
                "Unexpected error: requested_instance should be of type DocIngestProcessorModel."
            )

        return requested_instance

    def get_or_create_doc_loader_instance(
        self,
        parent_domain: Optional[DomainModel] = None,
        parent_source: Optional[SourceModel] = None,
        id: Optional[int] = None,
        name: Optional[str] = None,
        config: dict[str, Any] = {},
    ) -> DocLoaderModel:
        if parent_domain or parent_source:
            parent_instance = self.parse_parent_instance(
                parent_domain=parent_domain,
                parent_source=parent_source,
            )
            list_of_model_instances = parent_instance.doc_loaders
            requested_instance = self.get_model_instance(
                list_of_model_instances=list_of_model_instances,
                id=id,
                name=name,
            )
        else:
            if not name:
                raise Exception("Unexpected error: name should not be None at this point.")
            provider_class_model = self.get_service_provider_class_model(
                list_of_service_providers=DocLoadingService.REQUIRED_CLASSES,
                requested_provider_name=name,
            )
            requested_instance = DocLoaderModel(
                name=name,
                config=provider_class_model.ClassConfigModel(**config).model_dump(),
            )
            DocIndex.session.flush()
        if not isinstance(requested_instance, DocLoaderModel):
            raise Exception(
                "Unexpected error: requested_instance should be of type DocLoaderModel."
            )

        return requested_instance

    def get_or_create_doc_db_instance(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        config: dict[str, Any] = {},
    ) -> DocDBModel:
        list_of_model_instances = self.index.doc_dbs
        requested_instance = self.get_model_instance(
            list_of_model_instances=list_of_model_instances,
            id=id,
            name=name,
        )
        if requested_instance is None:
            if not name:
                raise Exception("Unexpected error: name should not be None at this point.")
            provider_class_model = self.get_service_provider_class_model(
                list_of_service_providers=DatabaseService.REQUIRED_CLASSES,
                requested_provider_name=name,
            )

            requested_instance = DocDBModel(
                name=name,
                config=provider_class_model.ClassConfigModel(**config).model_dump(),
            )
            DocIndex.session.flush()
        if not isinstance(requested_instance, DocDBModel):
            raise Exception(
                "Unexpected error: requested_instance should be of type DocLoaderModel."
            )

        return requested_instance

    def get_template_instance(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> DocIndexTemplateModel:
        list_of_model_instances = self.index.doc_index_templates
        requested_instance = self.get_model_instance(
            list_of_model_instances=list_of_model_instances,
            id=id,
            name=name,
        )
        if not isinstance(requested_instance, DocIndexTemplateModel):
            raise Exception(
                "Unexpected error: requested_instance should be of type DocLoaderModel."
            )

        return requested_instance

    def get_domain_instance(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> DomainModel:
        requested_instance = self.get_model_instance(
            list_of_model_instances=self.index.domains,
            id=id,
            name=name,
        )
        if not isinstance(requested_instance, DomainModel):
            raise Exception(
                "Unexpected error: requested_instance should be of type DocLoaderModel."
            )

        return requested_instance

    def get_source_instance(
        self,
        parent_domain: Optional[DomainModel] = None,
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> SourceModel:
        if parent_domain is None:
            parent_domain = self.domain

        requested_instance = self.get_model_instance(
            list_of_model_instances=parent_domain.sources,
            id=id,
            name=name,
        )
        if not isinstance(requested_instance, SourceModel):
            raise Exception(
                "Unexpected error: requested_instance should be of type DocLoaderModel."
            )

        return requested_instance

    def get_model_instance(
        self,
        list_of_model_instances: Union[
            list[DomainModel],
            list[SourceModel],
            list[DocIndexTemplateModel],
            list[DocDBModel],
            list[DocLoaderModel],
            list[DocIngestProcessorModel],
        ],
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Union[
        DomainModel,
        SourceModel,
        DocIndexTemplateModel,
        DocDBModel,
        DocLoaderModel,
        DocIngestProcessorModel,
    ]:
        if id:
            if (
                requested_instance := next(
                    (instance for instance in list_of_model_instances if instance.id == id),
                    None,
                )
            ) is None:
                raise Exception(f"id {id} not found in {list_of_model_instances}.")
        elif name:
            if (
                requested_instance := next(
                    (instance for instance in list_of_model_instances if instance.name == name),
                    None,
                )
            ) is None:
                raise Exception(f"name {name} not found in {list_of_model_instances}.")
        else:
            raise Exception("Unexpected error: id or name should not be None at this point.")

        if requested_instance is None:
            raise Exception("Unexpected error: domain should not be None at this point.")

        return requested_instance

    def set_current_domain_or_source_provider_instance(
        self,
        domain_or_source: Union[Type[DomainModel], Type[SourceModel]],
        set_model_type: Union[
            Type[DocDBModel], Type[DocLoaderModel], Type[DocIngestProcessorModel]
        ],
        set_id: Optional[int] = None,
        set_name: Optional[str] = None,
    ):
        if domain_or_source is DomainModel:
            parent_domain = self.domain
            parent_source = None
            parent_instance = self.domain
        elif domain_or_source is SourceModel:
            parent_domain = None
            parent_source = self.source
            parent_instance = self.source
        else:
            raise Exception(f"Unexpected error: {domain_or_source.__name__} not found.")
        if set_model_type is DocDBModel:
            set_instance = self.get_or_create_doc_db_instance(id=set_id, name=set_name)
            parent_instance.enabled_doc_db = set_instance
        elif set_model_type is DocLoaderModel:
            set_instance = self.get_or_create_doc_loader_instance(
                parent_domain=parent_domain, parent_source=parent_source, id=set_id, name=set_name
            )
            parent_instance.enabled_doc_loader = set_instance
        elif set_model_type is DocIngestProcessorModel:
            set_instance = self.get_or_create_doc_ingest_processor_instance(
                parent_domain=parent_domain, parent_source=parent_source, id=set_id, name=set_name
            )
            parent_instance.enabled_doc_ingest_processor = set_instance
        else:
            raise Exception(f"Unexpected error: {set_model_type.__name__} not found.")

        DocIndex.session.flush()

    def create_domain(
        self,
        new_name: Optional[str] = None,
        new_description: Optional[str] = None,
        requested_template_name: Optional[str] = None,
        clone_name: Optional[str] = None,
        clone_id: Optional[int] = None,
    ) -> DomainModel:
        if not new_name:
            new_name = DomainModel.DEFAULT_NAME
        new_name = self.check_and_handle_name_collision(
            existing_names=self.list_of_all_context_index_domain_names, new_name=new_name
        )
        if not new_description:
            new_description = DomainModel.DEFAULT_DESCRIPTION
        new_instance = DomainModel(name=new_name, description=new_description)

        DocIndex.doc_index_model.domains.append(new_instance)
        DocIndex.session.flush()

        if not self.index.current_domain:
            self.index.current_domain = new_instance
            DocIndex.session.flush()
        if not clone_name and not clone_id:
            if not requested_template_name:
                requested_template_name = new_instance.DEFAULT_TEMPLATE_NAME
            context_template = self.get_template_instance(
                name=requested_template_name,
            )
            self.set_domain_or_source_config(
                target_instance=new_instance,
                enabled_doc_ingest_processor_name=context_template.enabled_doc_ingest_processor_name,
                enabled_doc_loader_name=context_template.enabled_doc_loader_name,
                enabled_doc_db_name=context_template.enabled_doc_db.name,
                batch_update_enabled=context_template.batch_update_enabled,
            )
            self.create_source(parent_domain=new_instance)
        else:
            object_to_clone = self.get_domain_instance(
                id=clone_id,
                name=clone_name,
            )

            for source_model_to_clone in object_to_clone.sources:
                self.create_source(
                    parent_domain=new_instance,
                    clone_name=source_model_to_clone.name,
                    clone_id=source_model_to_clone.id,
                )

            self.set_domain_or_source_config(
                target_instance=new_instance,
                enabled_doc_ingest_processor_name=object_to_clone.enabled_doc_ingest_processor.name,
                enabled_doc_loader_name=object_to_clone.enabled_doc_loader.name,
                enabled_doc_db_name=object_to_clone.enabled_doc_db.name,
                batch_update_enabled=object_to_clone.batch_update_enabled,
            )

        self.populate_service_providers(
            target_instance=new_instance, requested_model_type=DocLoaderModel
        )
        self.populate_service_providers(
            target_instance=new_instance, requested_model_type=DocIngestProcessorModel
        )

        return new_instance

    def create_source(
        self,
        parent_domain: DomainModel,
        new_name: Optional[str] = None,
        new_description: Optional[str] = None,
        requested_template_name: Optional[str] = None,
        clone_name: Optional[str] = None,
        clone_id: Optional[int] = None,
    ) -> SourceModel:
        if not new_name:
            new_name = SourceModel.DEFAULT_NAME
        new_name = self.check_and_handle_name_collision(
            existing_names=parent_domain.list_of_source_names, new_name=new_name
        )
        if not new_description:
            new_description = SourceModel.DEFAULT_DESCRIPTION
        new_instance = SourceModel(name=new_name, description=new_description)

        parent_domain.sources.append(new_instance)
        DocIndex.session.flush()

        if not parent_domain.current_source:
            parent_domain.current_source = new_instance
            DocIndex.session.flush()
        if not clone_name and not clone_id:
            if not requested_template_name:
                requested_template_name = new_instance.DEFAULT_TEMPLATE_NAME
            context_template = self.get_template_instance(
                name=requested_template_name,
            )

            self.set_domain_or_source_config(
                target_instance=new_instance,
                enabled_doc_ingest_processor_name=context_template.enabled_doc_ingest_processor_name,
                enabled_doc_loader_name=context_template.enabled_doc_loader_name,
                enabled_doc_db_name=context_template.enabled_doc_db.name,
                batch_update_enabled=context_template.batch_update_enabled,
            )
        else:
            object_to_clone = self.get_source_instance(
                parent_domain=parent_domain,
                id=clone_id,
                name=clone_name,
            )

            self.set_domain_or_source_config(
                target_instance=new_instance,
                enabled_doc_ingest_processor_name=object_to_clone.enabled_doc_ingest_processor.name,
                enabled_doc_loader_name=object_to_clone.enabled_doc_loader.name,
                enabled_doc_db_name=object_to_clone.enabled_doc_db.name,
                batch_update_enabled=object_to_clone.batch_update_enabled,
            )

        self.populate_service_providers(
            target_instance=new_instance, requested_model_type=DocLoaderModel
        )
        self.populate_service_providers(
            target_instance=new_instance, requested_model_type=DocIngestProcessorModel
        )

        return new_instance

    def set_domain_or_source_config(
        self,
        target_instance: Union[DomainModel, SourceModel],
        batch_update_enabled: bool,
        enabled_doc_ingest_processor_name: Optional[str] = None,
        enabled_doc_loader_name: Optional[str] = None,
        enabled_doc_loader_config: dict = {},
        enabled_doc_db_name: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        if name:
            target_instance.name = name
        if description:
            target_instance.description = description
        target_instance.batch_update_enabled = batch_update_enabled
        if enabled_doc_loader_name is None:
            enabled_doc_loader_name = DocLoaderModel.DEFAULT_DOC_LOADER_NAME
        enabled_doc_loader = self.get_or_create_doc_loader_instance(
            name=enabled_doc_loader_name,
            config=enabled_doc_loader_config,
        )
        if not isinstance(enabled_doc_loader, DocLoaderModel):
            raise Exception(
                "Unexpected error: enabled_doc_loader should be of type DocLoaderModel."
            )
        target_instance.doc_loaders.append(enabled_doc_loader)
        DocIndex.session.flush()
        target_instance.enabled_doc_loader = enabled_doc_loader

        if enabled_doc_ingest_processor_name is None:
            enabled_doc_ingest_processor_name = (
                DocIngestProcessorModel.DEFAULT_DOC_INGEST_PROCESSOR_NAME
            )
        enabled_doc_ingest_processor = self.get_or_create_doc_ingest_processor_instance(
            name=enabled_doc_ingest_processor_name,
            config=enabled_doc_loader_config,
        )
        if not isinstance(enabled_doc_ingest_processor, DocIngestProcessorModel):
            raise Exception(
                "Unexpected error: enabled_doc_ingest_processor should be of type DocIngestProcessorModel."
            )
        target_instance.doc_ingest_processors.append(enabled_doc_ingest_processor)
        DocIndex.session.flush()
        target_instance.enabled_doc_ingest_processor = enabled_doc_ingest_processor

        if enabled_doc_db_name is None:
            enabled_doc_db_name = DocDBModel.DEFAULT_DOC_DB_NAME
        target_instance.enabled_doc_db = self.get_or_create_doc_db_instance(
            name=enabled_doc_db_name
        )
        DocIndex.session.flush()

    def get_service_provider_class_model(
        self,
        list_of_service_providers: list[Any],
        requested_provider_name: str,
    ):
        if (
            provider_class_model := next(
                (
                    object
                    for object in list_of_service_providers
                    if object.CLASS_NAME == requested_provider_name
                ),
                None,
            )
        ) is None:
            raise Exception(
                f"name {requested_provider_name} not found in {list_of_service_providers}."
            )

        return provider_class_model

    def populate_service_providers(
        self,
        target_instance: Union[DomainModel, SourceModel],
        requested_model_type: Union[Type[DocLoaderModel], Type[DocIngestProcessorModel]],
    ):
        if requested_model_type is DocLoaderModel:
            list_of_available_providers = DocLoadingService.REQUIRED_CLASSES
            list_of_current_providers = target_instance.doc_loaders
            for available_provider_class in list_of_available_providers:
                if available_provider_class.CLASS_NAME in [
                    current_provider.name for current_provider in list_of_current_providers
                ]:
                    continue
                list_of_current_providers.append(
                    self.get_or_create_doc_loader_instance(  # type: ignore
                        name=available_provider_class.CLASS_NAME,
                    )
                )
        elif requested_model_type is DocIngestProcessorModel:
            list_of_available_providers = IngestProcessingService.REQUIRED_CLASSES
            list_of_current_providers = target_instance.doc_ingest_processors
            for available_provider_class in list_of_available_providers:
                if available_provider_class.CLASS_NAME in [
                    current_provider.name for current_provider in list_of_current_providers
                ]:
                    continue
                list_of_current_providers.append(
                    self.get_or_create_doc_ingest_processor_instance(  # type: ignore
                        name=available_provider_class.CLASS_NAME,
                    )
                )
        else:
            raise Exception(f"Unexpected error: {requested_model_type.__name__} not found.")

        DocIndex.session.flush()

    def add_doc_dbs_to_index(self):
        for db_class in DatabaseService.REQUIRED_CLASSES:
            doc_db_provider_name = db_class.CLASS_NAME
            existing_config = next(
                (
                    doc_db
                    for doc_db in DocIndex.doc_index_model.doc_dbs
                    if doc_db.name == doc_db_provider_name
                ),
                None,
            )

            if not existing_config:
                db_config = db_class.ClassConfigModel().model_dump()
                DocIndex.doc_index_model.doc_dbs.append(
                    DocDBModel(name=doc_db_provider_name, config=db_config)
                )
                DocIndex.session.flush()

    def add_default_context_templates_to_index(self):
        for available_template in DocIndexTemplates.AVAILABLE_TEMPLATES:
            existing_config = next(
                (
                    index_context_template
                    for index_context_template in DocIndex.doc_index_model.doc_index_templates
                    if index_context_template.name == available_template.TEMPLATE_NAME
                ),
                None,
            )
            if not existing_config:
                enabled_doc_db = self.get_or_create_doc_db_instance(
                    name=available_template.doc_db_provider_name
                )
                if not isinstance(enabled_doc_db, DocDBModel):
                    raise Exception(
                        "Unexpected error: enabled_doc_db should not be of type DocDBModel."
                    )
                new_template = self.create_template(
                    new_template_name=available_template.TEMPLATE_NAME,
                    enabled_doc_ingest_processor_name=available_template.doc_ingest_processor_provider_name,
                    enabled_doc_ingest_processor_config=available_template.doc_ingest_processor_config.model_dump(),
                    enabled_doc_loader_name=available_template.doc_loader_provider_name,
                    enabled_doc_loader_config=available_template.doc_loader_config.model_dump(),
                    enabled_doc_db=enabled_doc_db,
                    batch_update_enabled=available_template.batch_update_enabled,
                )

                DocIndex.doc_index_model.doc_index_templates.append(new_template)
                DocIndex.session.flush()

    def save_config_as_template(
        self,
        parent_object: Union[DomainModel, SourceModel],
        new_template_name: Optional[str] = None,
    ):
        if not new_template_name:
            new_template_name = parent_object.name

        new_context_template_name = self.check_and_handle_name_collision(
            existing_names=DocIndex.doc_index_model.list_of_doc_index_template_names,
            new_name=new_template_name,
        )
        new_template = self.create_template(
            new_template_name=new_context_template_name,
            enabled_doc_ingest_processor_name=parent_object.enabled_doc_ingest_processor.name,
            enabled_doc_ingest_processor_config=parent_object.enabled_doc_ingest_processor.config,
            enabled_doc_loader_name=parent_object.enabled_doc_loader.name,
            enabled_doc_loader_config=parent_object.enabled_doc_loader.config,
            enabled_doc_db=parent_object.enabled_doc_db,
            batch_update_enabled=parent_object.batch_update_enabled,
        )

        # Append it to the index's list of context_configs
        DocIndex.doc_index_model.doc_index_templates.append(new_template)
        DocIndex.session.flush()

    def create_template(
        self,
        new_template_name: str,
        enabled_doc_ingest_processor_name: str,
        enabled_doc_ingest_processor_config: dict,
        enabled_doc_loader_name: str,
        enabled_doc_loader_config: dict,
        enabled_doc_db: DocDBModel,
        batch_update_enabled: bool,
    ):
        return DocIndexTemplateModel(
            name=new_template_name,
            enabled_doc_ingest_processor_name=enabled_doc_ingest_processor_name,
            enabled_doc_ingest_processor_config=enabled_doc_ingest_processor_config,
            enabled_doc_loader_name=enabled_doc_loader_name,
            enabled_doc_loader_config=enabled_doc_loader_config,
            enabled_doc_db=enabled_doc_db,
            batch_update_enabled=batch_update_enabled,
        )

    @staticmethod
    def check_and_handle_name_collision(existing_names: list[str], new_name: str) -> str:
        i = 0
        test_name = new_name
        while test_name in existing_names:
            test_name = f"{new_name}_{i}"
            i += 1
        return test_name

    # def ingest_docs(self,
    #     target_instance: Union[DomainModel, SourceModel],

    #                 ):
