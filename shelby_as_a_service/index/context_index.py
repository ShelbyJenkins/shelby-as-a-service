from typing import Any, Optional, Type, Union

from index.context_models import Base, ContextModel, DocDBConfigs, DocLoaderConfigs, DomainModel, SourceModel
from index.index_base import IndexBase
from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class ContextIndex(IndexBase):
    model: ContextModel
    session: Session

    def __init__(self) -> None:
        IndexBase.setup_index()
        self.get_session()
        self.setup_context_index()

    def setup_context_index(self):
        if not (context_index := self.session.query(ContextModel).first()):
            self.session.add(ContextModel())
            if not (context_index := self.session.query(ContextModel).first()):
                raise Exception("Context index not found.")

        self.populate_doc_db_configs(context_index)
        self.populate_doc_loader_configs(context_index)

        if not (domains := context_index.domains):
            default_domain = DomainModel(
                enabled_doc_db_name=context_index.enabled_doc_db_name,
                enabled_doc_loader_name=context_index.enabled_doc_loader_name,
            )
            context_index.domains.append(default_domain)
            self.populate_doc_loader_configs(default_domain)

        if not domains[0].sources:
            default_source = SourceModel(
                enabled_doc_db_name=domains[0].enabled_doc_db_name,
                enabled_doc_loader_name=domains[0].enabled_doc_loader_name,
            )
            domains[0].sources.append(default_source)
            self.populate_doc_loader_configs(default_source)

        self.model = context_index
        self.commit_session()
        self.session.add(self.model)

    @property
    def list_of_domain_names(self) -> list:
        return [domain.name for domain in self.model.domains]

    def domain(self, domain_name: Optional[str] = None) -> "Domain":
        if not domain_name:
            domain_name = self.model.current_domain_name
        domain_model = next((domain for domain in self.model.domains if domain.name == domain_name), None)
        if not domain_model:
            raise Exception(f"Domain {domain_name} not found.")
        return Domain(domain_model)

    @property
    def list_of_doc_loading_names(self) -> list:
        return [doc_db.CLASS_NAME for doc_db in DocLoadingService.REQUIRED_CLASSES]

    @property
    def doc_loading(self) -> DocLoadingService:
        # doc_loading_name = self.model.current_doc_loading_name or self.model.CURRENT_DOC_LOADING_NAME
        return DocLoadingService()

        # raise Exception(f"Document DB {doc_loading_name} has no ClassConfigModel.")

    @property
    def list_of_db_names(self) -> list:
        return [doc_db.CLASS_NAME for doc_db in DocumentDBService.REQUIRED_CLASSES]

    @property
    def doc_db(self) -> DocumentDBService:
        db_name = self.model.enabled_doc_db_name or self.model.DEFAULT_DB_NAME

        if doc_db := self.session.query(DocDBConfigs).filter_by(db_name=db_name).first():
            if db_config := doc_db.db_config:
                return DocumentDBService(db_config)
        raise Exception(f"Document DB {db_name} has no ClassConfigModel.")

    @property
    def doc_db_provider(self) -> DocumentDBService:
        db_name = self.model.enabled_doc_db_name or self.model.DEFAULT_DB_NAME
        if not db_name:
            db_name = self.model.DEFAULT_DB_NAME

        if doc_db := self.session.query(DocDBConfigs).filter_by(db_name=db_name).first():
            if db_config := doc_db.db_config:
                doc_db_service = DocumentDBService(db_config)
                doc_db_provider = doc_db_service.get_requested_class_instance(
                    doc_db_service.list_of_class_instances, db_name
                )
                return doc_db_provider
        raise Exception(f"Document DB {db_name} has no ClassConfigModel.")

    # def set_doc_db(self, db_name: Optional[str] = None):
    #         doc_db_class = self.get_doc_db(db_name)
    #         if hasattr(doc_db_class, "ClassConfigModel"):
    #             return doc_db_class.ClassConfigModel().model_dump()
    #         raise Exception(f"Document DB {db_name} has no ClassConfigModel.")


class Domain(ContextIndex):
    model: DomainModel

    def __init__(self, domain_model) -> None:
        self.model = domain_model

    @property
    def list_of_source_names(self) -> list:
        return [source.name for source in self.model.sources]

    def source(self, source_name: Optional[str] = None) -> "Source":
        if not source_name:
            source_name = self.model.current_source_name
        source_model = next((source for source in self.model.sources if source.name == source_name), None)
        if not source_model:
            raise Exception(f"Source {source_name} not found.")
        return Source(source_model)


class Source(Domain):
    model: SourceModel

    def __init__(self, source_model) -> None:
        self.model = source_model
