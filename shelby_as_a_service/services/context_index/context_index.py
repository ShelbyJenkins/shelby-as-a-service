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
    ContextConfigModel,
    ContextIndexModel,
    ContextTemplateModel,
    DocDBModel,
    DocLoaderModel,
    DomainModel,
    SourceModel,
)
from .context_templates import ContextTemplates


def check_and_handle_name_collision(existing_names: list[str], new_name: str) -> str:
    if new_name not in existing_names:
        return new_name
    existing_name = new_name
    i = 0
    while existing_name == new_name:
        new_name = f"{new_name}_{i}"
        i += 1
    return new_name


class ContextConfig:
    instance_model: Union[DomainModel, SourceModel]

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
                        requested_database_name=available_template.database_provider_name
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

    def get_template(
        self,
        requested_template_id: Optional[int] = None,
        requested_template_name: Optional[str] = None,
    ) -> ContextTemplateModel:
        # get template
        if requested_template_id:
            if (
                requested_context_template := next(
                    (
                        context_template
                        for context_template in ContextIndex.context_index_model.index_context_templates
                        if context_template.id == requested_template_id
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"DocDB {requested_template_id} not found in {self.instance_model}."
                )
        else:
            if (
                requested_context_template := next(
                    (
                        context_template
                        for context_template in ContextIndex.context_index_model.index_context_templates
                        if context_template.context_template_name == requested_template_name
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"DocDB {requested_template_name} not found in {self.instance_model}."
                )

        return requested_context_template

    def set_context_config_from_template(
        self,
        requested_template_id: Optional[int] = None,
        requested_template_name: Optional[str] = None,
    ):
        requested_context_template = self.get_template(
            requested_template_id=requested_template_id,
            requested_template_name=requested_template_name,
        )

        existing_context_config_names = [
            existing_config.context_config_name
            for existing_config in self.instance_model.context_configs
        ]

        new_context_config_name = check_and_handle_name_collision(
            existing_names=existing_context_config_names,
            new_name=requested_context_template.context_template_name,
        )

        # create new context_config from template
        new_context_config = ContextConfigModel(
            context_config_name=new_context_config_name,
            doc_db_id=requested_context_template.doc_db_id,
            batch_update_enabled=requested_context_template.batch_update_enabled,
        )
        # Append it to the class's list of context_configs
        self.instance_model.context_configs.append(new_context_config)
        ContextIndex.session.flush()
        self.instance_model.context_config_id = new_context_config.id
        ContextIndex.session.flush()
        DocLoading.add_doc_loaders_to_config_or_template(
            enabled_doc_loader_name=requested_context_template.doc_loader.doc_loader_provider_name,
            enabled_doc_loader_config=requested_context_template.doc_loader.doc_loader_config,
            context_config_or_template=new_context_config,
        )

    def get_config(
        self,
        requested_config_id: Optional[int] = None,
        requested_config_name: Optional[str] = None,
    ) -> ContextConfigModel:
        # get config
        if requested_config_id:
            if (
                requested_context_config := next(
                    (
                        context_config
                        for context_config in self.instance_model.context_configs
                        if context_config.id == requested_config_id
                    ),
                    None,
                )
            ) is None:
                raise Exception(f"DocDB {requested_config_id} not found in {self.instance_model}.")
        else:
            if (
                requested_context_config := next(
                    (
                        context_config
                        for context_config in self.instance_model.context_configs
                        if context_config.context_config_name == requested_config_name
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"DocDB {requested_config_name} not found in {self.instance_model}."
                )

        return requested_context_config

    def save_config_as_template(
        self,
        requested_config_id: Optional[int] = None,
        requested_config_name: Optional[str] = None,
    ):
        requested_context_config = self.get_config(
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

    def clone_config(
        self,
        existing_context_config: ContextConfigModel,
        target_instance_model: Union[DomainModel, SourceModel],
    ):
        new_context_config = ContextConfigModel(
            context_config_name=existing_context_config.context_config_name,
            doc_db_id=existing_context_config.doc_db_id,
            batch_update_enabled=existing_context_config.batch_update_enabled,
        )

        target_instance_model.context_configs.append(new_context_config)
        ContextIndex.session.flush()
        DocLoading.add_doc_loaders_to_config_or_template(
            enabled_doc_loader_name=existing_context_config.doc_loader.doc_loader_provider_name,
            enabled_doc_loader_config=existing_context_config.doc_loader.doc_loader_config,
            context_config_or_template=new_context_config,
        )

    def set_config(
        self,
        requested_config_id: Optional[int] = None,
        requested_config_name: Optional[str] = None,
    ):
        requested_context_config = self.get_config(
            requested_config_id=requested_config_id,
            requested_config_name=requested_config_name,
        )
        self.instance_model.context_config_id = requested_context_config.id
        ContextIndex.session.flush()


class DocDB:
    @staticmethod
    def add_doc_dbs_to_index():
        for db_class in DataBaseService.REQUIRED_CLASSES:
            database_provider_name = db_class.CLASS_NAME
            existing_config = next(
                (
                    doc_db
                    for doc_db in ContextIndex.context_index_model.doc_dbs
                    if doc_db.database_provider_name == database_provider_name
                ),
                None,
            )

            if not existing_config:
                db_config = db_class.ClassConfigModel().model_dump()
                ContextIndex.context_index_model.doc_dbs.append(
                    DocDBModel(database_provider_name=database_provider_name, db_config=db_config)
                )
                ContextIndex.session.flush()

    @staticmethod
    def get_doc_db(
        requested_database_id: Optional[int] = None,
        requested_database_name: Optional[str] = None,
    ) -> DocDBModel:
        if requested_database_id:
            doc_db = next(
                (
                    doc_db
                    for doc_db in ContextIndex.context_index_model.doc_dbs
                    if doc_db.id == requested_database_id
                ),
                None,
            )
            if doc_db is None:
                raise Exception(
                    f"DocDB {requested_database_id} not found in {ContextIndex.context_index_model.doc_dbs}"
                )
        else:
            doc_db = next(
                (
                    doc_db
                    for doc_db in ContextIndex.context_index_model.doc_dbs
                    if doc_db.database_provider_name == requested_database_name
                ),
                None,
            )
            if doc_db is None:
                raise Exception(
                    f"DocDB {requested_database_name} not found in {ContextIndex.context_index_model.doc_dbs}"
                )
        return doc_db


class DocLoading:
    @staticmethod
    def add_doc_loaders_to_config_or_template(
        enabled_doc_loader_name,
        enabled_doc_loader_config,
        context_config_or_template: Union[ContextConfigModel, ContextTemplateModel],
    ):
        for available_doc_loader in DocLoadingService.REQUIRED_CLASSES:
            if available_doc_loader.CLASS_NAME == enabled_doc_loader_name:
                doc_loader_config = enabled_doc_loader_config
            else:
                doc_loader_config = available_doc_loader.ClassConfigModel().model_dump()

            context_config_or_template.doc_loaders.append(
                DocLoaderModel(
                    doc_loader_provider_name=available_doc_loader.CLASS_NAME,
                    doc_loader_config=doc_loader_config,
                )
            )
            ContextIndex.session.flush()

        DocLoading.set_doc_loader(
            context_config_or_template=context_config_or_template,
            requested_doc_loader_name=enabled_doc_loader_name,
        )

    @staticmethod
    def set_doc_loader(
        context_config_or_template: Union[ContextConfigModel, ContextTemplateModel],
        requested_doc_loader_id: Optional[int] = None,
        requested_doc_loader_name: Optional[str] = None,
    ):
        doc_loader = DocLoading.get_doc_loader(
            list_of_doc_loaders=context_config_or_template.doc_loaders,
            requested_doc_loader_id=requested_doc_loader_id,
            requested_doc_loader_name=requested_doc_loader_name,
        )

        context_config_or_template.doc_loader_id = doc_loader.id
        ContextIndex.session.flush()

    @staticmethod
    def get_doc_loader(
        list_of_doc_loaders: list[DocLoaderModel],
        requested_doc_loader_id: Optional[int] = None,
        requested_doc_loader_name: Optional[str] = None,
    ) -> DocLoaderModel:
        if requested_doc_loader_id:
            doc_loader = next(
                (
                    doc_loader
                    for doc_loader in list_of_doc_loaders
                    if doc_loader.id == requested_doc_loader_id
                ),
                None,
            )
            if doc_loader is None:
                raise Exception(
                    f"DocDB {requested_doc_loader_id} not found in {list_of_doc_loaders}"
                )
        else:
            doc_loader = next(
                (
                    doc_loader
                    for doc_loader in list_of_doc_loaders
                    if doc_loader.doc_loader_provider_name == requested_doc_loader_name
                ),
                None,
            )
            if doc_loader is None:
                raise Exception(
                    f"DocDB {requested_doc_loader_name} not found in {list_of_doc_loaders}"
                )
        return doc_loader


class ContextIndex(IndexBase, ContextConfig, DocDB):
    context_index_model: ContextIndexModel
    session: Session
    log: logging.Logger
    instance_model: Union[DomainModel, SourceModel]
    context_config: ContextConfigModel
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
    def list_of_domain_names(self) -> list:
        return [domain.name for domain in ContextIndex.context_index_model.domains]

    @property
    def domain(self) -> "DomainInstance":
        if getattr(ContextIndex.context_index_model, "domain", None) is None:
            raise Exception(f"{ContextIndex.context_index_model} has no domain.")
        return DomainInstance(domain_model=ContextIndex.context_index_model.domain)

    @property
    def list_of_all_context_index_source_names(self) -> list:
        all_sources = ContextIndex.session.query(SourceModel).all()
        return [source.name for source in all_sources]

    @property
    def context_config_name(self) -> str:
        return self.instance_model.context_config.context_config_name

    @property
    def list_of_context_config_names(self) -> list:
        return [
            context_config.context_config_name
            for context_config in self.instance_model.context_configs
        ]

    @property
    def list_of_context_template_names(self) -> list:
        return [
            context_template.context_template_name
            for context_template in ContextIndex.context_index_model.index_context_templates
        ]

    # @property
    # def doc_ingest(self) -> DocLoadingService:

    #     if loader_config := getattr(enabled_doc_ingest_template, "loader_config", None):
    #         raise Exception(f"{enabled_doc_ingest_template} has no loader_config.")
    #     return DocLoadingService(
    #         config_file_dict=loader_config,
    #         doc_loading_provider=enabled_doc_ingest_template.loader_name,
    #     )

    @property
    def doc_database_provider_name(self) -> str:
        if (enabled_doc_db := getattr(self.instance_model, "enabled_doc_db", None)) is None:
            raise Exception(f"{self.instance_model} has no enabled_doc_db.")
        if database_provider_name := getattr(enabled_doc_db, "database_provider_name", None):
            raise Exception(f"{enabled_doc_db} has no database_provider_name.")
        if database_provider_name is None:
            raise Exception(
                "Unexpected error: database_provider_name should not be None at this point."
            )
        return database_provider_name

    @property
    def list_of_database_provider_names(self) -> list:
        return [
            doc_db.database_provider_name for doc_db in ContextIndex.context_index_model.doc_dbs
        ]

    @property
    def list_of_doc_loader_provider_names(self) -> list:
        return [
            doc_loader.doc_loader_provider_name
            for doc_loader in self.instance_model.context_config.doc_loaders
        ]

    @property
    def doc_db(self) -> DataBaseService:
        if (context_config := getattr(self.instance_model, "context_config", None)) is None:
            raise Exception(f"{self.instance_model} has no context_config.")
        if (doc_db := getattr(context_config, "doc_db", None)) is None:
            raise Exception(f"{context_config} has no doc_db.")
        if (db_config := getattr(doc_db, "db_config", None)) is None:
            raise Exception(f"{doc_db} has no db_config.")
        return DataBaseService(
            config_file_dict=db_config, database_provider=self.doc_database_provider_name
        )

    def create_domain(
        self,
        new_domain_name: Optional[str] = None,
        requested_template_name: Optional[str] = None,
    ):
        if new_domain_name is None:
            new_domain_name = DomainModel.DEFAULT_DOMAIN_NAME
        new_domain_name = check_and_handle_name_collision(
            existing_names=self.list_of_domain_names, new_name=new_domain_name
        )
        default_domain = DomainModel(name=new_domain_name)
        ContextIndex.context_index_model.domains.append(default_domain)
        ContextIndex.session.flush()
        if not ContextIndex.context_index_model.domain_id:
            self.set_domain()

        if not requested_template_name:
            requested_template_name = default_domain.DEFAULT_TEMPLATE_NAME
        self.domain.set_context_config_from_template(
            requested_template_name=requested_template_name
        )

        self.domain.create_source()

    def clone_domain(
        self,
        new_domain_name: Optional[str] = None,
        clone_domain_name: Optional[str] = None,
        clone_domain_id: Optional[int] = None,
    ):
        domain_instance_to_clone = self.get_domain(
            requested_domain_id=clone_domain_id, requested_domain_name=clone_domain_name
        )
        if new_domain_name is None:
            new_domain_name = domain_instance_to_clone.domain_model.name
        if new_domain_name is None:
            new_domain_name = DomainModel.DEFAULT_DOMAIN_NAME
        new_domain_name = check_and_handle_name_collision(
            existing_names=self.list_of_domain_names, new_name=new_domain_name
        )
        domain_model_clone = DomainModel(name=new_domain_name)
        ContextIndex.context_index_model.domains.append(domain_model_clone)
        ContextIndex.session.flush()
        for existing_context_config in self.instance_model.context_configs:
            domain_instance_to_clone.clone_config(
                existing_context_config=existing_context_config,
                target_instance_model=domain_model_clone,
            )
        self.set_config(
            requested_config_name=domain_instance_to_clone.instance_model.context_config.context_config_name
        )
        domain_instance_clone = DomainInstance(domain_model=domain_model_clone)
        for source_model_to_clone in domain_instance_to_clone.domain_model.sources:
            source_instance_to_clone = SourceInstance(source_model=source_model_to_clone)
            domain_instance_clone.clone_source(
                new_source_name=source_model_to_clone.name,
                source_instance_to_clone=source_instance_to_clone,
            )

    def set_domain(self, domain_id: Optional[int] = None, domain_name: Optional[str] = None):
        domain = self.get_domain(requested_domain_id=domain_id, requested_domain_name=domain_name)

        ContextIndex.context_index_model.domain_id = domain.domain_model.id
        ContextIndex.session.flush()

    def get_domain(
        self, requested_domain_id: Optional[int] = None, requested_domain_name: Optional[str] = None
    ) -> "DomainInstance":
        if requested_domain_id:
            if (
                requested_domain := next(
                    (
                        domain
                        for domain in ContextIndex.context_index_model.domains
                        if domain.id == requested_domain_id
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"requested_domain_id {requested_domain_id} not found in {ContextIndex.context_index_model.domains}."
                )
        elif requested_domain_name:
            if (
                requested_domain := next(
                    (
                        domain
                        for domain in ContextIndex.context_index_model.domains
                        if domain.name == requested_domain_name
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"requested_domain_name {requested_domain_name} not found in {ContextIndex.context_index_model.domains}."
                )
        else:
            if (
                requested_domain := next(
                    (
                        domain
                        for domain in ContextIndex.context_index_model.domains
                        if domain.name == DomainModel.DEFAULT_DOMAIN_NAME
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"DEFAULT_DOMAIN_NAME {DomainModel.DEFAULT_DOMAIN_NAME} not found in {DomainModel}."
                )

        if requested_domain is None:
            raise Exception("Unexpected error: domain should not be None at this point.")

        return DomainInstance(domain_model=requested_domain)


class DomainInstance(ContextIndex):
    domain_model: DomainModel
    context_index: ContextIndex

    def __init__(self, domain_model) -> None:
        self.domain_model = domain_model

    @property
    def instance_model(self) -> DomainModel:
        return self.domain_model

    @property
    def list_of_source_names(self) -> list:
        return [source.name for source in self.domain_model.sources]

    @property
    def source(self) -> "SourceInstance":
        if getattr(self.domain_model, "source", None) is None:
            raise Exception(f"{self.domain_model} has no source.")
        return SourceInstance(self.domain_model.source)

    def create_source(
        self,
        new_source_name: Optional[str] = None,
        requested_template_name: Optional[str] = None,
    ):
        if new_source_name is None:
            new_source_name = SourceModel.DEFAULT_SOURCE_NAME
        new_source_name = check_and_handle_name_collision(
            existing_names=self.list_of_source_names, new_name=new_source_name
        )
        default_source = SourceModel(name=new_source_name)
        self.domain_model.sources.append(default_source)
        ContextIndex.session.flush()
        if not self.domain_model.source_id:
            self.set_source()

        if requested_template_name:
            if not requested_template_name:
                requested_template_name = default_source.DEFAULT_TEMPLATE_NAME
            self.set_context_config_from_template(requested_template_name=requested_template_name)
        else:
            self.clone_config(
                existing_context_config=self.instance_model.context_config,
                target_instance_model=default_source,
            )
            self.source.set_config(
                requested_config_name=self.domain_model.context_config.context_config_name
            )

    def clone_source(
        self,
        new_source_name: Optional[str] = None,
        clone_source_name: Optional[str] = None,
        clone_source_id: Optional[int] = None,
        source_instance_to_clone: Optional["SourceInstance"] = None,
    ):
        if source_instance_to_clone is None:
            if clone_source_name or clone_source_id:
                source_instance_to_clone = self.get_source(
                    requested_source_id=clone_source_id, requested_source_name=clone_source_name
                )
                if new_source_name is None:
                    new_source_name = source_instance_to_clone.source_model.name

        if new_source_name is None:
            new_source_name = SourceModel.DEFAULT_SOURCE_NAME
        new_source_name = check_and_handle_name_collision(
            existing_names=self.list_of_source_names, new_name=new_source_name
        )
        source_model_clone = SourceModel(name=new_source_name)
        self.domain_model.sources.append(source_model_clone)
        ContextIndex.session.flush()
        if source_instance_to_clone is None:
            raise Exception(
                "Unexpected error: source_instance_to_clone should not be None at this point."
            )

        for existing_context_config in source_instance_to_clone.source_model.context_configs:
            source_instance_to_clone.clone_config(
                existing_context_config=existing_context_config,
                target_instance_model=source_model_clone,
            )

        self.source.set_config(
            requested_config_name=source_instance_to_clone.source_model.context_config.context_config_name
        )

    def set_source(self, source_id: Optional[int] = None, source_name: Optional[str] = None):
        source = self.get_source(requested_source_id=source_id, requested_source_name=source_name)
        self.domain_model.source_id = source.source_model.id
        ContextIndex.session.flush()

    def get_source(
        self, requested_source_id: Optional[int] = None, requested_source_name: Optional[str] = None
    ) -> "SourceInstance":
        if requested_source_id:
            if (
                requested_source := next(
                    (
                        source
                        for source in self.domain_model.sources
                        if source.id == requested_source_id
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"requested_source_id {requested_source_id} not found in {self.domain_model.sources}."
                )
        elif requested_source_name:
            if (
                requested_source := next(
                    (
                        source
                        for source in self.domain_model.sources
                        if source.name == requested_source_name
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"requested_source_name {requested_source_name} not found in {self.domain_model.sources}."
                )
        else:
            if (
                requested_source := next(
                    (
                        source
                        for source in self.domain_model.sources
                        if source.name == SourceModel.DEFAULT_SOURCE_NAME
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"DEFAULT_SOURCE_NAME {SourceModel.DEFAULT_SOURCE_NAME} not found in {SourceModel}."
                )

        if requested_source is None:
            raise Exception("Unexpected error: source should not be None at this point.")

        return SourceInstance(source_model=requested_source)


class SourceInstance(DomainInstance):
    source_model: SourceModel

    def __init__(self, source_model) -> None:
        self.source_model = source_model

    @property
    def instance_model(self) -> SourceModel:
        return self.source_model
