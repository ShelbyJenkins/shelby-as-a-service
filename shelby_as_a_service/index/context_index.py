import logging
from typing import Any, Optional, Type, Union

from agents.ingest.ingest_templates import IngestTemplates
from index.context_index_model import (
    ContextModel,
    DocDBConfigs,
    DocIngestTemplateConfigs,
    DomainModel,
    SourceModel,
)
from index.index_base import IndexBase
from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

log: logging.Logger = logging.getLogger(__name__)


class ContextIndex(IndexBase):
    context_index_model: ContextModel
    session: Session

    def __init__(self) -> None:
        IndexBase.setup_index()
        self.session = IndexBase.get_session()
        try:
            self.setup_context_index()
        except SQLAlchemyError:  # Catch any SQLAlchemy exceptions
            self.session.rollback()  # Roll back the transaction
            raise  # Re-raise the caught exception

    def setup_context_index(self):
        if context_index_model := self.session.query(ContextModel).first():
            self.context_index_model = context_index_model
            DocDB.update_doc_db_configs(context_index=self)
            DocIngest.update_doc_ingest_configs(context_index=self)
        else:
            self.context_index_model = ContextModel()
            self.session.add(self.context_index_model)
            self.session.flush()
            DocDB.update_doc_db_configs(context_index=self)
            DocDB.set_doc_db(class_instance=self.context_index_model, context_index=self)

            DocIngest.setup_doc_ingest_configs(
                class_instance=self.context_index_model, context_index=self
            )
            DocIngest.set_doc_ingest_template(
                class_instance=self.context_index_model, context_index=self
            )

            self.create_domain()
            self.set_domain()
            self.domain.create_source()
            self.domain.set_source()

        self.commit_context_index()

    def commit_context_index(self):
        self.session = self.commit_session()
        self.session.add(self.context_index_model)

    @property
    def model(self) -> ContextModel:
        return self.context_index_model

    @property
    def list_of_domain_names(self) -> list:
        return [domain.name for domain in self.context_index_model.domains]

    @property
    def domain(self) -> "DomainInstance":
        if getattr(self.context_index_model, "enabled_domain", None) is None:
            raise Exception(f"{self.context_index_model} has no enabled_domain.")
        return DomainInstance(self.context_index_model.enabled_domain, context_index=self)

    @property
    def doc_ingest_name(self) -> str:
        if (
            enabled_doc_ingest_template := getattr(self.model, "enabled_doc_ingest_template", None)
        ) is None:
            raise Exception(f"{self.model} has no enabled_doc_ingest_template.")
        if ingest_template_name := getattr(
            enabled_doc_ingest_template, "ingest_template_name", None
        ):
            raise Exception(f"{enabled_doc_ingest_template} has no ingest_template_name.")
        if ingest_template_name is None:
            raise Exception(
                "Unexpected error: ingest_template_name should not be None at this point."
            )
        return ingest_template_name

    @property
    def list_of_ingest_template_names(self) -> list:
        return [
            ingest_template.ingest_template_name
            for ingest_template in self.model.doc_ingest_templates
        ]

    @property
    def doc_ingest(self) -> DocLoadingService:
        if (
            enabled_doc_ingest_template := getattr(self.model, "enabled_doc_ingest_template", None)
        ) is None:
            raise Exception(f"{self.model} has no enabled_doc_ingest_template.")
        if loader_config := getattr(enabled_doc_ingest_template, "loader_config", None):
            raise Exception(f"{enabled_doc_ingest_template} has no loader_config.")
        return DocLoadingService(
            config_file_dict=loader_config,
            doc_loading_provider=enabled_doc_ingest_template.loader_name,
        )

    @property
    def doc_db_name(self) -> str:
        if (enabled_doc_db := getattr(self.model, "enabled_doc_db", None)) is None:
            raise Exception(f"{self.model} has no enabled_doc_db.")
        if db_name := getattr(enabled_doc_db, "db_name", None):
            raise Exception(f"{enabled_doc_db} has no db_name.")
        if db_name is None:
            raise Exception("Unexpected error: db_name should not be None at this point.")
        return db_name

    @property
    def list_of_db_names(self) -> list:
        return [doc_db.db_name for doc_db in self.context_index_model.doc_dbs]

    @property
    def doc_db(self) -> DocumentDBService:
        if (enabled_doc_db := getattr(self.model, "enabled_doc_db", None)) is None:
            raise Exception(f"{self.model} has no enabled_doc_db.")
        if db_config := getattr(enabled_doc_db, "db_config", None):
            raise Exception(f"{enabled_doc_db} has no db_config.")
        return DocumentDBService(config_file_dict=db_config, database_provider=self.doc_db_name)

    def create_domain(self, domain_name: Optional[str] = None):
        if domain_name is None:
            domain_name = DomainModel.DEFAULT_DOMAIN_NAME
        default_domain = DomainModel(name=domain_name)
        self.context_index_model.domains.append(default_domain)
        self.session.flush()
        DocDB.set_doc_db(
            class_instance=default_domain,
            context_index=self,
            db_id=self.context_index_model.enabled_doc_db_id,
        )

        DocIngest.setup_doc_ingest_configs(class_instance=default_domain, context_index=self)
        DocIngest.set_doc_ingest_template(
            class_instance=default_domain,
            context_index=self,
            ingest_id=self.context_index_model.enabled_doc_ingest_template_id,
        )
        self.session.flush()

    def set_domain(self, domain_id: Optional[int] = None, domain_name: Optional[str] = None):
        if domain_id:
            if (
                domain := next(
                    (
                        domain
                        for domain in self.context_index_model.domains
                        if domain.id == domain_id
                    ),
                    None,
                )
            ) is None:
                raise Exception(f"DocDB {domain_id} not found.")
        elif domain_name:
            if (
                domain := next(
                    (
                        domain
                        for domain in self.context_index_model.domains
                        if domain.name == domain_name
                    ),
                    None,
                )
            ) is None:
                raise Exception(f"DocDB {domain_name} not found.")
        else:
            if (
                domain := next(
                    (
                        domain
                        for domain in self.context_index_model.domains
                        if domain.name == DomainModel.DEFAULT_DOMAIN_NAME
                    ),
                    None,
                )
            ) is None:
                raise Exception(f"DocDB {DomainModel.DEFAULT_DOMAIN_NAME} not found.")

        if domain is None:
            raise Exception("Unexpected error: domain should not be None at this point.")

        self.context_index_model.enabled_domain_id = domain.id
        self.session.flush()


class DomainInstance(ContextIndex):
    domain_model: DomainModel
    context_index: ContextIndex

    def __init__(self, domain_model, context_index: ContextIndex) -> None:
        self.domain_model = domain_model
        self.context_index = context_index

    @property
    def model(self) -> DomainModel:
        return self.domain_model

    @property
    def list_of_source_names(self) -> list:
        return [source.name for source in self.domain_model.sources]

    @property
    def source(self) -> "SourceInstance":
        if getattr(self.domain_model, "enabled_source", None) is None:
            raise Exception(f"{self.domain_model} has no enabled_source.")
        return SourceInstance(self.domain_model.enabled_source)

    def create_source(self):
        default_source = SourceModel()
        self.domain_model.sources.append(default_source)
        self.context_index.session.flush()
        DocDB.set_doc_db(
            class_instance=default_source,
            context_index=self.context_index,
            db_id=self.model.enabled_doc_db_id,
        )
        DocIngest.setup_doc_ingest_configs(
            class_instance=default_source, context_index=self.context_index
        )
        DocIngest.set_doc_ingest_template(
            class_instance=default_source,
            context_index=self.context_index,
            ingest_id=self.model.enabled_doc_ingest_template_id,
        )
        self.context_index.session.flush()

    def set_source(self, source_id: Optional[int] = None, source_name: Optional[str] = None):
        if source_id:
            if (
                source := next(
                    (source for source in self.domain_model.sources if source.id == source_id), None
                )
            ) is None:
                raise Exception(f"DocDB {source_id} not found in {self}.")
        elif source_name:
            if (
                source := next(
                    (source for source in self.domain_model.sources if source.name == source_name),
                    None,
                )
            ) is None:
                raise Exception(f"DocDB {source_name} not found in {self}.")
        else:
            if (
                source := next(
                    (
                        source
                        for source in self.domain_model.sources
                        if source.name == SourceModel.DEFAULT_SOURCE_NAME
                    ),
                    None,
                )
            ) is None:
                raise Exception(f"DocDB {SourceModel.DEFAULT_SOURCE_NAME} not found in {self}.")

        if source is None:
            raise Exception("Unexpected error: source should not be None at this point.")

        self.domain_model.enabled_source_id = source.id
        self.context_index.session.flush()


class SourceInstance(DomainInstance):
    source_model: SourceModel

    def __init__(self, source_model) -> None:
        self.source_model = source_model

    @property
    def model(self) -> SourceModel:
        return self.source_model


class DocDB(ContextIndex):
    doc_dbs: list[DocDBConfigs]

    @classmethod
    def update_doc_db_configs(cls, context_index: ContextIndex):
        cls.doc_dbs = context_index.session.query(DocDBConfigs).all()

        for db_class in DocumentDBService.REQUIRED_CLASSES:
            db_name = db_class.CLASS_NAME
            existing_config = next(
                (doc_db for doc_db in cls.doc_dbs if doc_db.db_name == db_name), None
            )

            if not existing_config:
                db_config = db_class.ClassConfigModel().model_dump()
                context_index.context_index_model.doc_dbs.append(
                    DocDBConfigs(db_name=db_name, db_config=db_config)
                )
                context_index.session.flush()
        cls.doc_dbs = context_index.session.query(DocDBConfigs).all()

    @staticmethod
    def set_doc_db(
        class_instance: Union[ContextModel, DomainModel, SourceModel],
        context_index: ContextIndex,
        db_id: Optional[int] = None,
        db_name: Optional[str] = None,
    ):
        if db_id:
            if (
                doc_db := next(
                    (
                        doc_db
                        for doc_db in context_index.context_index_model.doc_dbs
                        if doc_db.id == db_id
                    ),
                    None,
                )
            ) is None:
                raise Exception(f"DocDB {db_id} not found in {class_instance}.")
        elif db_name:
            if (
                doc_db := next(
                    (
                        doc_db
                        for doc_db in context_index.context_index_model.doc_dbs
                        if doc_db.db_name == db_name
                    ),
                    None,
                )
            ) is None:
                raise Exception(f"DocDB {db_name} not found in {class_instance}.")
        else:
            if (
                doc_db := next(
                    (
                        doc_db
                        for doc_db in context_index.context_index_model.doc_dbs
                        if doc_db.db_name == context_index.context_index_model.DEFAULT_DB_NAME
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"DocDB {context_index.context_index_model.DEFAULT_DB_NAME} not found in {class_instance}."
                )

        if doc_db is None:
            raise Exception("Unexpected error: doc_db should not be None at this point.")

        class_instance.enabled_doc_db_id = doc_db.id
        context_index.session.flush()


class DocIngest(ContextIndex):
    @classmethod
    def update_doc_ingest_configs(cls, context_index: ContextIndex):
        DocIngest.setup_doc_ingest_configs(
            class_instance=context_index.context_index_model, context_index=context_index
        )
        domains = context_index.session.query(DomainModel).all()
        for domain in domains:
            DocIngest.setup_doc_ingest_configs(class_instance=domain, context_index=context_index)
        sources = context_index.session.query(SourceModel).all()
        for source in sources:
            DocIngest.setup_doc_ingest_configs(class_instance=source, context_index=context_index)

    @staticmethod
    def setup_doc_ingest_configs(
        class_instance: Union[ContextModel, DomainModel, SourceModel], context_index: ContextIndex
    ):
        for template_class in IngestTemplates.AVAILABLE_TEMPLATES:
            existing_config = next(
                (
                    doc_ingest_template
                    for doc_ingest_template in class_instance.doc_ingest_templates
                    if doc_ingest_template.ingest_template_name == template_class.TEMPLATE_NAME
                ),
                None,
            )
            if not existing_config:
                loader_config = template_class.doc_loader_class.ClassConfigModel().model_dump()
                loader_name = template_class.doc_loader_class.CLASS_NAME
                new_config = DocIngestTemplateConfigs(
                    ingest_template_name=template_class.TEMPLATE_NAME,
                    loader_config=loader_config,
                    loader_name=loader_name,
                )
                class_instance.doc_ingest_templates.append(new_config)
                context_index.session.flush()

    @staticmethod
    def set_doc_ingest_template(
        class_instance: Union[ContextModel, DomainModel, SourceModel],
        context_index: ContextIndex,
        ingest_id: Optional[int] = None,
        ingest_template_name: Optional[str] = None,
    ):
        if ingest_id:
            if (
                doc_ingest_template := next(
                    (
                        doc_ingest_template
                        for doc_ingest_template in class_instance.doc_ingest_templates
                        if doc_ingest_template.id == ingest_id
                    ),
                    None,
                )
            ) is None:
                doc_ingest_template = DocIngest.clone_template(
                    class_instance=class_instance, context_index=context_index, ingest_id=ingest_id
                )
        elif ingest_template_name:
            if (
                doc_ingest_template := next(
                    (
                        doc_ingest_template
                        for doc_ingest_template in class_instance.doc_ingest_templates
                        if doc_ingest_template.ingest_template_name == ingest_template_name
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"ingest_template_name: {ingest_template_name} not found in {class_instance}."
                )
        else:
            if (
                doc_ingest_template := next(
                    (
                        doc_ingest_template
                        for doc_ingest_template in class_instance.doc_ingest_templates
                        if doc_ingest_template.ingest_template_name
                        == context_index.context_index_model.DEFAULT_INGEST_TEMPLATE_NAME
                    ),
                    None,
                )
            ) is None:
                raise Exception(
                    f"DocIngest {context_index.context_index_model.DEFAULT_INGEST_TEMPLATE_NAME} not found."
                )

        if doc_ingest_template is None:
            raise Exception(
                "Unexpected error: doc_ingest_template should not be None at this point."
            )

        class_instance.enabled_doc_ingest_template_id = doc_ingest_template.id
        context_index.session.flush()

    @staticmethod
    def clone_template(
        class_instance: Union[ContextModel, DomainModel, SourceModel],
        context_index: ContextIndex,
        ingest_id: int,
    ):
        cloned_doc_ingest_template = (
            context_index.session.query(DocIngestTemplateConfigs).filter_by(id=ingest_id).first()
        )

        if cloned_doc_ingest_template is None:
            raise Exception(f"ingest_id: {ingest_id} not found in DocIngestTemplateConfigs.")

        # Check if a template with the same name already exists in class_instance.doc_ingest_templates
        existing_doc_ingest_template = next(
            (
                doc_ingest_template
                for doc_ingest_template in class_instance.doc_ingest_templates
                if doc_ingest_template.ingest_template_name
                == cloned_doc_ingest_template.ingest_template_name
            ),
            None,
        )

        if existing_doc_ingest_template:
            class_instance.doc_ingest_templates.remove(existing_doc_ingest_template)
            context_index.session.flush()

        new_config = DocIngestTemplateConfigs(
            ingest_template_name=cloned_doc_ingest_template.ingest_template_name,
            loader_name=cloned_doc_ingest_template.loader_name,
            loader_config=cloned_doc_ingest_template.loader_config,
        )

        class_instance.doc_ingest_templates.append(new_config)

        context_index.session.flush()

        return new_config
