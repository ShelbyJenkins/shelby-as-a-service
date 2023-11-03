import logging
from typing import Any, Optional, Type, Union

from services.database.database_service import DataBaseService
from services.database.index_base import IndexBase
from services.document_loading.document_loading_providers import (
    GenericRecursiveWebScraper,
    GenericWebScraper,
)
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .context_index_model import (
    ContextIndexModel,
    ContextTemplateModel,
    DocDBModel,
    DocLoaderModel,
    DomainModel,
    SourceModel,
)
from .context_templates import ContextTemplates


def check_and_handle_name_collision(existing_names: list[str], new_name: str) -> str:
    i = 0
    test_name = new_name
    while test_name in existing_names:
        test_name = f"{new_name}_{i}"
        i += 1
    return test_name


class ContextIndex(IndexBase):
    context_index_model: ContextIndexModel
    session: Session
    log: logging.Logger
    object_model: Union[DomainModel, SourceModel]
    context_template: ContextTemplateModel

    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)

        ContextIndex.setup_index()
        ContextIndex.session = ContextIndex.get_session()
        try:
            self.setup_context_index()
        except SQLAlchemyError:
            ContextIndex.session.rollback()
            raise

    def setup_context_index(self):
        if context_index_model := self.session.query(ContextIndexModel).first():
            ContextIndex.context_index_model = context_index_model
            self.add_doc_dbs_to_index()
            self.add_default_context_templates_to_index()
        else:
            ContextIndex.context_index_model = ContextIndexModel()
            ContextIndex.session.add(ContextIndex.context_index_model)
            ContextIndex.session.flush()

            self.add_doc_dbs_to_index()
            self.add_default_context_templates_to_index()

            self.create_domain()

        ContextIndex.commit_context_index()

    @staticmethod
    def commit_context_index():
        ContextIndex.session = ContextIndex.commit_session(ContextIndex.session)
        ContextIndex.session.add(ContextIndex.context_index_model)

    @property
    def list_of_all_context_index_domain_names(self) -> list:
        return [domain.name for domain in ContextIndex.context_index_model.domains]

    @property
    def index(self) -> "ContextIndexModel":
        return ContextIndex.context_index_model

    @property
    def domain(self) -> "DomainModel":
        if getattr(ContextIndex.context_index_model, "current_domain", None) is None:
            raise Exception(f"{ContextIndex.context_index_model} has no domain.")
        return ContextIndex.context_index_model.current_domain

    @property
    def source(self) -> "SourceModel":
        if getattr(self.domain, "source", None) is None:
            raise Exception(f"{self.domain} has no source.")
        return self.domain.current_source

    @property
    def list_of_all_context_index_source_names(self) -> list:
        all_sources = ContextIndex.session.query(SourceModel).all()
        return [source.name for source in all_sources]

    def parse_parent_object(
        self,
        parent_domain: Optional[DomainModel] = None,
        parent_source: Optional[SourceModel] = None,
    ) -> Union[DomainModel, SourceModel]:
        if (parent_source is not None) != (parent_domain is not None):
            parent_object = parent_source if parent_source is not None else parent_domain
        else:
            raise Exception(
                "Unexpected error: Either parent_source or parent_domain must be set, but not both or neither."
            )
        if parent_object is None:
            raise Exception("Unexpected error: parent_object should not be None at this point.")
        return parent_object

    def get_model_object(
        self,
        requested_model_type: Union[
            Type[DomainModel],
            Type[SourceModel],
            Type[ContextTemplateModel],
            Type[DocDBModel],
            Type[DocLoaderModel],
        ],
        parent_domain: Optional[DomainModel] = None,
        parent_source: Optional[SourceModel] = None,
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Union[DomainModel, SourceModel, ContextTemplateModel, DocDBModel, DocLoaderModel]:
        if requested_model_type is DomainModel:
            list_of_model_objects = ContextIndex.context_index_model.domains
        elif requested_model_type is SourceModel:
            if parent_domain is None:
                raise Exception("Unexpected error: parent_domain should not be None at this point.")
            list_of_model_objects = parent_domain.sources
        elif requested_model_type is ContextTemplateModel:
            list_of_model_objects = self.index.index_context_templates
        elif requested_model_type is DocDBModel:
            list_of_model_objects = ContextIndex.context_index_model.doc_dbs
        elif requested_model_type is DocLoaderModel:
            parent_object = self.parse_parent_object(
                parent_domain=parent_domain, parent_source=parent_source
            )
            list_of_model_objects = parent_object.doc_loaders

        else:
            raise Exception(f"Unexpected error: {requested_model_type.__name__} not found.")

        if id:
            if (
                requested_object := next(
                    (object for object in list_of_model_objects if object.id == id),
                    None,
                )
            ) is None:
                raise Exception(f"id {id} not found in {list_of_model_objects}.")
        elif name:
            if (
                requested_object := next(
                    (object for object in list_of_model_objects if object.name == name),
                    None,
                )
            ) is None:
                raise Exception(f"name {name} not found in {list_of_model_objects}.")
        else:
            raise Exception("Unexpected error: id or name should not be None at this point.")

        if requested_object is None:
            raise Exception("Unexpected error: domain should not be None at this point.")

        return requested_object

    def set_object(
        self,
        set_model_type: Union[
            Type[DomainModel], Type[SourceModel], Type[DocDBModel], Type[DocLoaderModel]
        ],
        parent_domain: Optional[DomainModel] = None,
        parent_source: Optional[SourceModel] = None,
        set_id: Optional[int] = None,
        set_name: Optional[str] = None,
    ):
        if set_model_type is DomainModel:
            set_object = self.get_model_object(DomainModel, id=set_id, name=set_name)
            ContextIndex.context_index_model.current_domain = set_object
        elif set_model_type is SourceModel:
            if parent_domain is None:
                raise Exception("Unexpected error: parent_domain should not be None at this point.")
            set_object = self.get_model_object(
                SourceModel, parent_domain=parent_domain, id=set_id, name=set_name
            )
            parent_domain.current_source = set_object
        elif set_model_type is DocDBModel:
            set_object = self.get_model_object(
                DocDBModel,
                parent_domain=parent_domain,
                parent_source=parent_source,
                id=set_id,
                name=set_name,
            )
            parent_object = self.parse_parent_object(
                parent_domain=parent_domain, parent_source=parent_source
            )
            parent_object.enabled_doc_db = set_object
        elif set_model_type is DocLoaderModel:
            set_object = self.get_model_object(
                DocLoaderModel,
                parent_domain=parent_domain,
                parent_source=parent_source,
                id=set_id,
                name=set_name,
            )
            parent_object = self.parse_parent_object(
                parent_domain=parent_domain, parent_source=parent_source
            )
            parent_object.enabled_doc_loader = set_object
        else:
            raise Exception(f"Unexpected error: {set_model_type.__name__} not found.")

        ContextIndex.session.flush()

    def create_domain(
        self,
        new_name: Optional[str] = None,
        new_description: Optional[str] = None,
        requested_template_name: Optional[str] = None,
        clone_name: Optional[str] = None,
        clone_id: Optional[int] = None,
    ) -> tuple[str, int]:
        if not new_name:
            new_name = DomainModel.DEFAULT_NAME
        new_name = check_and_handle_name_collision(
            existing_names=self.list_of_all_context_index_domain_names, new_name=new_name
        )
        if not new_description:
            new_description = DomainModel.DEFAULT_DESCRIPTION
        new_model = DomainModel(name=new_name, description=new_description)

        ContextIndex.context_index_model.domains.append(new_model)
        ContextIndex.session.flush()

        if not ContextIndex.context_index_model.current_domain:
            self.set_object(set_model_type=DomainModel, set_id=new_model.id)

        if not clone_name and not clone_id:
            if not requested_template_name:
                requested_template_name = new_model.DEFAULT_TEMPLATE_NAME
            context_template = self.get_model_object(
                ContextTemplateModel,
                name=requested_template_name,
            )
            if context_template is not ContextTemplateModel:
                raise Exception(
                    "Unexpected error: context_template should not be of type ContextTemplateModel."
                )
            self.set_domain_or_source_config(
                target_object=new_model,
                enabled_doc_loader_name=context_template.enabled_doc_loader_name,
                enabled_doc_db_name=context_template.enabled_doc_db.name,
                batch_update_enabled=context_template.batch_update_enabled,
            )
            self.create_source(parent_domain=new_model)
        else:
            object_to_clone = self.get_model_object(
                requested_model_type=DomainModel,
                id=clone_id,
                name=clone_name,
            )
            if not isinstance(object_to_clone, DomainModel):
                raise Exception("Unexpected error: object_to_clone should be of type DomainModel.")
            for source_model_to_clone in object_to_clone.sources:
                self.create_source(
                    parent_domain=new_model,
                    clone_name=source_model_to_clone.name,
                    clone_id=source_model_to_clone.id,
                )

            self.set_domain_or_source_config(
                target_object=new_model,
                enabled_doc_loader_name=object_to_clone.enabled_doc_loader.name,
                enabled_doc_db_name=object_to_clone.enabled_doc_db.name,
                batch_update_enabled=object_to_clone.batch_update_enabled,
            )

        self.populate_service_providers(
            target_object=new_model, requested_model_type=DocLoaderModel
        )

        return new_model.name, new_model.id

    def create_source(
        self,
        parent_domain: DomainModel,
        new_name: Optional[str] = None,
        new_description: Optional[str] = None,
        requested_template_name: Optional[str] = None,
        clone_name: Optional[str] = None,
        clone_id: Optional[int] = None,
    ) -> tuple[str, int]:
        if not new_name:
            new_name = SourceModel.DEFAULT_NAME
        new_name = check_and_handle_name_collision(
            existing_names=self.list_of_all_context_index_domain_names, new_name=new_name
        )
        if not new_description:
            new_description = SourceModel.DEFAULT_DESCRIPTION
        new_model = SourceModel(name=new_name, description=new_description)

        parent_domain.sources.append(new_model)
        ContextIndex.session.flush()

        if not ContextIndex.context_index_model.current_domain:
            self.set_object(set_model_type=SourceModel, set_id=new_model.id)

        if not clone_name and not clone_id:
            if not requested_template_name:
                requested_template_name = new_model.DEFAULT_TEMPLATE_NAME
            context_template = self.get_model_object(
                ContextTemplateModel,
                name=requested_template_name,
                parent_domain=parent_domain,
            )
            if context_template is not ContextTemplateModel:
                raise Exception(
                    "Unexpected error: context_template should not be of type ContextTemplateModel."
                )
            self.set_domain_or_source_config(
                target_object=new_model,
                enabled_doc_loader_name=context_template.enabled_doc_loader_name,
                enabled_doc_db_name=context_template.enabled_doc_db.name,
                batch_update_enabled=context_template.batch_update_enabled,
            )
        else:
            object_to_clone = self.get_model_object(
                requested_model_type=SourceModel,
                id=clone_id,
                name=clone_name,
            )
            if object_to_clone is not SourceModel:
                raise Exception(
                    "Unexpected error: object_to_clone should not be of type SourceModel."
                )

            self.set_domain_or_source_config(
                target_object=new_model,
                enabled_doc_loader_name=object_to_clone.enabled_doc_loader.name,
                enabled_doc_db_name=object_to_clone.enabled_doc_db.name,
                batch_update_enabled=object_to_clone.batch_update_enabled,
            )

        self.populate_service_providers(
            target_object=new_model, requested_model_type=DocLoaderModel
        )

        return new_model.name, new_model.id

    def set_domain_or_source_config(
        self,
        target_object: Union[DomainModel, SourceModel],
        batch_update_enabled: bool,
        enabled_doc_loader_name: Optional[str] = None,
        enabled_doc_loader_config: Optional[dict] = None,
        enabled_doc_db_name: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        if name:
            target_object.name = name
        if description:
            target_object.description = description
        target_object.batch_update_enabled = batch_update_enabled
        if enabled_doc_loader_name is None:
            enabled_doc_loader_name = DocLoaderModel.DEFAULT_DOC_LOADER_NAME
        target_object.enabled_doc_loader = self.create_service_provider_model(
            requested_model_type=DocLoaderModel,
            requested_provider_name=enabled_doc_loader_name,
            config=enabled_doc_loader_config,
        )
        if enabled_doc_db_name is None:
            enabled_doc_db_name = DocDBModel.DEFAULT_DOC_DB_NAME
        target_object.enabled_doc_db = self.get_model_object(DocDBModel, name=enabled_doc_db_name)
        ContextIndex.session.flush()

    def create_service_provider_model(
        self,
        requested_model_type: Union[
            Type[DocLoaderModel],
            Type[DocDBModel],
        ],
        requested_provider_name: str,
        config: Optional[dict] = None,
    ):
        if requested_model_type is DocLoaderModel:
            list_of_service_providers = DocLoadingService.REQUIRED_CLASSES
            class_model = DocLoaderModel
        elif requested_model_type is DocDBModel:
            list_of_service_providers = DataBaseService.REQUIRED_CLASSES
            class_model = DocDBModel
        else:
            raise Exception(f"Unexpected error: {requested_model_type.__name__} not found.")

        if (
            requested_object := next(
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

        provider_model = class_model(
            name=requested_object.CLASS_NAME,
            config=requested_object.ClassConfigModel(**config).model_dump(),
        )
        return provider_model

    def populate_service_providers(
        self,
        target_object: Union[DomainModel, SourceModel],
        requested_model_type: Type[DocLoaderModel],
    ):
        if requested_model_type is DocLoaderModel:
            list_of_available_providers = DocLoadingService.REQUIRED_CLASSES
            list_of_current_providers = target_object.doc_loaders
        else:
            raise Exception(f"Unexpected error: {requested_model_type.__name__} not found.")

        for available_provider_class in list_of_available_providers:
            if available_provider_class.CLASS_NAME in [
                current_provider.name for current_provider in list_of_current_providers
            ]:
                continue
            list_of_current_providers.append(
                self.create_service_provider_model(  # type: ignore
                    requested_model_type=requested_model_type,
                    requested_provider_name=available_provider_class.CLASS_NAME,
                )
            )

            ContextIndex.session.flush()

    def add_doc_dbs_to_index(self):
        for db_class in DataBaseService.REQUIRED_CLASSES:
            doc_db_provider_name = db_class.CLASS_NAME
            existing_config = next(
                (
                    doc_db
                    for doc_db in ContextIndex.context_index_model.doc_dbs
                    if doc_db.name == doc_db_provider_name
                ),
                None,
            )

            if not existing_config:
                db_config = db_class.ClassConfigModel().model_dump()
                ContextIndex.context_index_model.doc_dbs.append(
                    DocDBModel(name=doc_db_provider_name, db_config=db_config)
                )
                ContextIndex.session.flush()

    def add_default_context_templates_to_index(self):
        for available_template in ContextTemplates.AVAILABLE_TEMPLATES:
            existing_config = next(
                (
                    index_context_template
                    for index_context_template in ContextIndex.context_index_model.index_context_templates
                    if index_context_template.name == available_template.TEMPLATE_NAME
                ),
                None,
            )
            if not existing_config:
                enabled_doc_db = self.get_model_object(
                    DocDBModel, name=available_template.doc_db_provider_name
                )
                if enabled_doc_db is not DocDBModel:
                    raise Exception(
                        "Unexpected error: enabled_doc_db should not be of type DocDBModel."
                    )
                new_template = self.create_template(
                    new_template_name=available_template.TEMPLATE_NAME,
                    enabled_doc_loader_name=available_template.doc_loader_provider_name,
                    enabled_doc_loader_config=available_template.doc_loader_config.model_dump(),
                    enabled_doc_db=enabled_doc_db,
                    batch_update_enabled=available_template.batch_update_enabled,
                )

                ContextIndex.context_index_model.index_context_templates.append(new_template)
                ContextIndex.session.flush()

    def save_config_as_template(
        self,
        parent_object: Union[DomainModel, SourceModel],
        new_template_name: Optional[str] = None,
    ):
        if not new_template_name:
            new_template_name = parent_object.name

        new_context_template_name = check_and_handle_name_collision(
            existing_names=ContextIndex.context_index_model.list_of_context_template_names,
            new_name=new_template_name,
        )
        new_template = self.create_template(
            new_template_name=new_context_template_name,
            enabled_doc_loader_name=parent_object.enabled_doc_loader.name,
            enabled_doc_loader_config=parent_object.enabled_doc_loader.config,
            enabled_doc_db=parent_object.enabled_doc_db,
            batch_update_enabled=parent_object.batch_update_enabled,
        )

        # Append it to the index's list of context_configs
        ContextIndex.context_index_model.index_context_templates.append(new_template)
        ContextIndex.session.flush()

    def create_template(
        self,
        new_template_name: str,
        enabled_doc_loader_name: str,
        enabled_doc_loader_config: dict,
        enabled_doc_db: DocDBModel,
        batch_update_enabled: bool,
    ):
        return ContextTemplateModel(
            name=new_template_name,
            enabled_doc_loader_name=enabled_doc_loader_name,
            enabled_doc_loader_config=enabled_doc_loader_config,
            enabled_doc_db=enabled_doc_db,
            batch_update_enabled=batch_update_enabled,
        )
