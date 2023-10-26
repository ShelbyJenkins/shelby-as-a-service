import logging
from typing import Any, Optional, Type, Union

from index.context_models import Base, ContextModel, DocDBConfigs, DomainModel, SourceModel
from index.index_base import IndexBase
from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

log: logging.Logger = logging.getLogger(__name__)


class ContextIndex(IndexBase):
    index_model: ContextModel
    session: Session

    def __init__(self) -> None:
        IndexBase.setup_index()
        self.get_session()
        self.setup_context_index()

    def setup_context_index(self):
        # Create a new context index from models
        if not (index_model := self.session.query(ContextModel).first()):
            self.index_model = ContextModel()
            self.session.add(self.index_model)
            self.session.flush()
            self.populate_doc_db_configs()
            enabled_doc_db = self.index_model.enabled_doc_db()
            self.index_model.enabled_doc_db_id = enabled_doc_db.id
            self.index_model.enabled_doc_db_name = enabled_doc_db.db_name

            default_domain_model = self.create_domain()
            self.enabled_domain_id = default_domain_model.id
            self.enabled_domain_name = default_domain_model.name

            default_source_model = self.domain.create_source()
            default_domain_model.enabled_source_id = default_source_model.id
            default_domain_model.enabled_source_name = default_source_model.name
        # Or update the existing one
        else:
            self.index_model = index_model
            self.populate_doc_db_configs()

        self.commit_session()
        self.session.add(self.index_model)

    def create_domain(self) -> "DomainModel":
        default_domain = DomainModel()
        self.index_model.domains.append(default_domain)
        default_domain.enabled_doc_db_id = self.index_model.enabled_doc_db_id
        default_domain.enabled_doc_db_name = self.index_model.enabled_doc_db_name
        self.session.flush()
        return default_domain

    @property
    def list_of_domain_names(self) -> list:
        return [domain.name for domain in self.index_model.domains]

    @property
    def domain(self) -> "Domain":
        if hasattr(self, "enabled_domain_relation") and self.index_model.enabled_domain_relation:
            return Domain(self.index_model.enabled_domain_relation)
        if enabled_domain_name := getattr(self, "enabled_domain_name", None):
            if domain_model := next(
                (domain for domain in self.index_model.domains if domain.name == enabled_domain_name), None
            ):
                return Domain(domain_model)
        # In the case of a first index creation we retrieve the default
        if domain_model := next(
            (domain for domain in self.index_model.domains if domain.name == DomainModel.DEFAULT_DOMAIN_NAME), None
        ):
            log.warning(f"domain {enabled_domain_name} not found. Using default {DomainModel.DEFAULT_DOMAIN_NAME}.")
            return Domain(domain_model)
        raise Exception("domain_model not found in index_model.")

    def populate_doc_db_configs(self):
        for db_class in DocumentDBService.REQUIRED_CLASSES:
            db_name = db_class.CLASS_NAME
            existing_config = next((doc_db for doc_db in self.index_model.doc_dbs if doc_db.db_name == db_name), None)

            if not existing_config:
                db_config = db_class.ClassConfigModel().model_dump()
                new_config = DocDBConfigs(context_id=self.index_model.id, db_name=db_name, db_config=db_config)
                self.index_model.doc_dbs.append(new_config)
                self.session.flush()

    @property
    def list_of_db_names(self) -> list:
        return [doc_db.CLASS_NAME for doc_db in DocumentDBService.REQUIRED_CLASSES]

    @property
    def doc_db(self) -> DocumentDBService:
        if model := getattr(self, "model", None):
            pass
        elif index_model := getattr(self, "index_model", None):
            model = index_model
        if enabled_doc_db_id := getattr(model, "enabled_doc_db_id", None):
            if doc_db := self.index_model.enabled_doc_db(enabled_doc_db_id):
                return DocumentDBService(doc_db.db_config)
            raise Exception(f"{model} has no doc_db for {enabled_doc_db_id}.")
        raise Exception(f"{model} has no enabled_doc_db_id.")


class Domain(ContextIndex):
    domain_model: DomainModel

    def __init__(self, domain_model) -> None:
        self.domain_model = domain_model

    def create_source(self) -> "SourceModel":
        default_source = SourceModel()
        self.domain_model.sources.append(default_source)
        default_source.enabled_doc_db_id = self.domain_model.enabled_doc_db_id
        default_source.enabled_doc_db_name = self.domain_model.enabled_doc_db_name
        self.session.flush()
        return default_source

    @property
    def list_of_source_names(self) -> list:
        return [source.name for source in self.domain_model.sources]

    @property
    def source(self) -> "Source":
        if hasattr(self, "enabled_source_relation") and self.domain_model.enabled_source_relation:
            return Source(self.domain_model.enabled_source_relation)
        if enabled_source_name := getattr(self, "enabled_source_name", None):
            if source_model := next(
                (source for source in self.domain_model.sources if source.name == enabled_source_name), None
            ):
                return Source(source_model)
        # In the case of a first index creation we retrieve the default
        if source_model := next(
            (source for source in self.domain_model.sources if source.name == SourceModel.DEFAULT_SOURCE_NAME), None
        ):
            log.warning(f"source {enabled_source_name} not found. Using default {SourceModel.DEFAULT_SOURCE_NAME}.")
            return Source(source_model)
        raise Exception("source_model not found in domain_model.")


class Source(Domain):
    model: SourceModel

    def __init__(self, source_model) -> None:
        self.source_model = source_model
