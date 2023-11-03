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
            DocDB.add_doc_dbs_to_index()
            self.add_default_context_templates_to_index()
        else:
            ContextIndex.context_index_model = ContextIndexModel()
            ContextIndex.session.add(ContextIndex.context_index_model)
            ContextIndex.session.flush()

            DocDB.add_doc_dbs_to_index()
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
            parent_object.ennabled_doc_db = set_object
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
        new_domain_name: Optional[str] = None,
        new_description: Optional[str] = None,
        requested_template_name: Optional[str] = None,
    ) -> tuple[str, int]:
        if not new_domain_name:
            new_domain_name = DomainModel.DEFAULT_DOMAIN_NAME
        new_domain_name = check_and_handle_name_collision(
            existing_names=self.list_of_all_context_index_domain_names, new_name=new_domain_name
        )
        if not new_description:
            new_description = DomainModel.DEFAULT_DOMAIN_DESCRIPTION
        new_domain_model = DomainModel(name=new_domain_name, description=new_description)
        ContextIndex.context_index_model.domains.append(new_domain_model)
        ContextIndex.session.flush()
        if not ContextIndex.context_index_model.current_domain_id:
            self.set_object(set_model_type=DomainModel, set_id=new_domain_model.id)

        if not requested_template_name:
            requested_template_name = new_domain_model.DEFAULT_TEMPLATE_NAME
        ContextConfig.set_context_config_from_template(
            object_model=new_domain_model, requested_template_name=requested_template_name
        )

        self.create_source(parent_domain=new_domain_model)

        return new_domain_model.name, new_domain_model.id

    def clone_domain(
        self,
        new_domain_name: Optional[str] = None,
        new_description: Optional[str] = None,
        clone_domain_name: Optional[str] = None,
        clone_domain_id: Optional[int] = None,
    ) -> tuple[str, int]:
        domain_instance_to_clone = self.get_domain(
            requested_domain_id=clone_domain_id, requested_domain_name=clone_domain_name
        )
        if not new_domain_name:
            new_domain_name = domain_instance_to_clone.domain_model.name
        if not new_domain_name:
            new_domain_name = DomainModel.DEFAULT_DOMAIN_NAME
        new_domain_name = check_and_handle_name_collision(
            existing_names=self.list_of_domain_names, new_name=new_domain_name
        )
        if not new_description:
            new_description = domain_instance_to_clone.domain_model.description
        domain_model_clone = DomainModel(name=new_domain_name, description=new_description)
        ContextIndex.context_index_model.domains.append(domain_model_clone)
        ContextIndex.session.flush()
        for existing_context_config in self.object_model.context_configs:
            ContextConfig.clone_config(
                existing_context_config=existing_context_config,
                target_object_model=domain_model_clone,
            )
        ContextConfig.set_config(
            object_model=domain_model_clone,
            requested_config_name=domain_instance_to_clone.object_model.context_config.context_config_name,
        )
        domain_instance_clone = DomainInstance(domain_model=domain_model_clone)
        for source_model_to_clone in domain_instance_to_clone.domain_model.sources:
            source_instance_to_clone = SourceInstance(source_model=source_model_to_clone)
            domain_instance_clone.clone_source(
                new_source_name=source_model_to_clone.name,
                source_instance_to_clone=source_instance_to_clone,
            )
        return domain_model_clone.name, domain_model_clone.id

    def create_source(
        self,
        parent_domain: DomainModel,
        new_source_name: Optional[str] = None,
        new_description: Optional[str] = None,
        requested_template_name: Optional[str] = None,
    ) -> tuple[str, int]:
        if not new_source_name:
            new_source_name = SourceModel.DEFAULT_SOURCE_NAME
        new_source_name = check_and_handle_name_collision(
            existing_names=parent_domain.list_of_source_names, new_name=new_source_name
        )
        if not new_description:
            new_description = SourceModel.DEFAULT_SOURCE_DESCRIPTION
        new_source_model = SourceModel(name=new_source_name, description=new_description)
        parent_domain.sources.append(new_source_model)
        ContextIndex.session.flush()
        if not parent_domain.current_source_id:
            self.set_object(set_model_type=SourceModel, set_id=new_source_model.id)

        if requested_template_name:
            if not requested_template_name:
                requested_template_name = new_source_model.DEFAULT_TEMPLATE_NAME
            ContextConfig.set_context_config_from_template(
                object_model=new_source_model, requested_template_name=requested_template_name
            )
        else:
            ContextConfig.clone_config(
                existing_context_config=self.object_model.context_config,
                target_object_model=new_source_model,
            )
            ContextConfig.set_config(
                object_model=new_source_model,
                requested_config_name=self.domain_model.context_config.context_config_name,
            )

        return new_source_model.name, new_source_model.id

    def clone_source(
        self,
        new_source_name: Optional[str] = None,
        new_description: Optional[str] = None,
        clone_source_name: Optional[str] = None,
        clone_source_id: Optional[int] = None,
        source_instance_to_clone: Optional["SourceInstance"] = None,
    ) -> tuple[str, int]:
        if source_instance_to_clone is None:
            if clone_source_name or clone_source_id:
                source_instance_to_clone = self.get_source(
                    requested_source_id=clone_source_id, requested_source_name=clone_source_name
                )
                if not new_source_name:
                    new_source_name = source_instance_to_clone.source_model.name

        if not new_source_name:
            new_source_name = SourceModel.DEFAULT_SOURCE_NAME
        new_source_name = check_and_handle_name_collision(
            existing_names=self.list_of_source_names, new_name=new_source_name
        )
        if not new_description:
            new_description = SourceModel.DEFAULT_SOURCE_DESCRIPTION
        source_model_clone = SourceModel(name=new_source_name, description=new_description)
        self.domain_model.sources.append(source_model_clone)
        ContextIndex.session.flush()
        if source_instance_to_clone is None:
            raise Exception(
                "Unexpected error: source_instance_to_clone should not be None at this point."
            )

        for existing_context_config in source_instance_to_clone.source_model.context_configs:
            ContextConfig.clone_config(
                existing_context_config=existing_context_config,
                target_object_model=source_model_clone,
            )

        ContextConfig.set_config(
            object_model=source_model_clone,
            requested_config_name=source_instance_to_clone.source_model.context_config.context_config_name,
        )

        return source_model_clone.name, source_model_clone.id

    def set_context_config_from_template(
        self,
        parent_object: Union[DomainModel, SourceModel],
        requested_template_id: Optional[int] = None,
        requested_template_name: Optional[str] = None,
    ):
        context_template = self.get_model_object(
            ContextTemplateModel,
            id=requested_template_id,
            name=requested_template_name,
        )
        if context_template is not ContextTemplateModel:
            raise Exception(
                "Unexpected error: context_template should not be of type ContextTemplateModel."
            )

        parent_object.enabled_doc_loader = context_template.enabled_doc_loader
        parent_object.ennabled_doc_db = context_template.ennabled_doc_db
        parent_object.batch_update_enabled = context_template.batch_update_enabled

        ContextIndex.session.flush()

        DocLoading.add_doc_loaders_to_config_or_template(
            enabled_doc_loader_name=requested_context_template.doc_loader.provider_name,
            enabled_doc_loader_config=requested_context_template.doc_loader.provider_config,
            context_config_or_template=new_context_config,
        )

    @staticmethod
    def add_default_context_templates_to_index():
        for available_template in ContextTemplates.AVAILABLE_TEMPLATES:
            existing_config = next(
                (
                    index_context_template
                    for index_context_template in ContextIndex.context_index_model.index_context_templates
                    if index_context_template.context_template_name
                    == available_template.TEMPLATE_NAME
                ),
                None,
            )
            if not existing_config:
                new_template = ContextTemplateModel(
                    context_template_name=available_template.TEMPLATE_NAME,
                    doc_db_id=DocDB.get_doc_db(
                        requested_database_name=available_template.provider_name
                    ).id,
                    batch_update_enabled=available_template.batch_update_enabled,
                )

                ContextIndex.context_index_model.index_context_templates.append(new_template)
                ContextIndex.session.flush()
                DocLoading.add_doc_loaders_to_config_or_template(
                    enabled_doc_loader_name=available_template.doc_loader_provider_name,
                    enabled_doc_loader_config=available_template.doc_loader_config.model_dump(),
                    context_config_or_template=new_template,
                )

    @staticmethod
    def save_config_as_template(
        object_model: Union[DomainModel, SourceModel],
        requested_config_id: Optional[int] = None,
        requested_config_name: Optional[str] = None,
    ):
        requested_context_config = ContextConfig.get_config(
            object_model=object_model,
            requested_config_id=requested_config_id,
            requested_config_name=requested_config_name,
        )
        existing_context_template_names = [
            existing_template.context_template_name
            for existing_template in ContextIndex.context_index_model.index_context_templates
        ]
        new_context_template_name = check_and_handle_name_collision(
            existing_names=existing_context_template_names,
            new_name=requested_context_config.context_config_name,
        )

        # create new context_config from template
        new_context_template = ContextTemplateModel(
            context_template_name=new_context_template_name,
            doc_db_id=requested_context_config.doc_db_id,
            batch_update_enabled=requested_context_config.batch_update_enabled,
        )
        # Append it to the index's list of context_configs
        ContextIndex.context_index_model.index_context_templates.append(new_context_template)
        ContextIndex.session.flush()

    @staticmethod
    def clone_config(
        existing_context_config: ContextConfigModel,
        target_object_model: Union[DomainModel, SourceModel],
    ):
        new_context_config = ContextConfigModel(
            context_config_name=existing_context_config.context_config_name,
            doc_db_id=existing_context_config.doc_db_id,
            batch_update_enabled=existing_context_config.batch_update_enabled,
        )

        target_object_model.context_configs.append(new_context_config)
        ContextIndex.session.flush()
        DocLoading.add_doc_loaders_to_config_or_template(
            enabled_doc_loader_name=existing_context_config.doc_loader.provider_name,
            enabled_doc_loader_config=existing_context_config.doc_loader.provider_config,
            context_config_or_template=new_context_config,
        )


class DocDB:
    @staticmethod
    def add_doc_dbs_to_index():
        for db_class in DataBaseService.REQUIRED_CLASSES:
            provider_name = db_class.CLASS_NAME
            existing_config = next(
                (
                    doc_db
                    for doc_db in ContextIndex.context_index_model.doc_dbs
                    if doc_db.provider_name == provider_name
                ),
                None,
            )

            if not existing_config:
                db_config = db_class.ClassConfigModel().model_dump()
                ContextIndex.context_index_model.doc_dbs.append(
                    DocDBModel(provider_name=provider_name, db_config=db_config)
                )
                ContextIndex.session.flush()


class DocLoading:
    @staticmethod
    def populate_context_index_default_template_with_doc_loader(
        enabled_doc_loader_name,
        enabled_doc_loader_config,
        context_template: ContextTemplateModel,
    ):
        for available_doc_loader in DocLoadingService.REQUIRED_CLASSES:
            if available_doc_loader.CLASS_NAME == enabled_doc_loader_name:
                doc_loader_config = enabled_doc_loader_config
            else:
                continue

            context_template.enabled_doc_loader = DocLoaderModel(
                provider_name=available_doc_loader.CLASS_NAME,
                provider_config=doc_loader_config,
            )

            ContextIndex.session.flush()
