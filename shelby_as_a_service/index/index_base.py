import os
from typing import Any, Optional, Type, Union

from app.app_base import AppBase
from index.context_models import Base, ContextModel, DocDBConfigs, DomainModel, SourceModel
from index.index_db import IndexDB
from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy.orm import Session, sessionmaker


class IndexBase(AppBase):
    CLASS_NAME: str = "index"
    local_index_dir: str
    index_db: Session

    @classmethod
    def setup_index(cls):
        cls.local_index_dir = os.path.join(cls.APP_DIR_PATH, cls.app_config.app_name, cls.CLASS_NAME)
        IndexDB.setup_index_db(cls.local_index_dir)

    @property
    def get_session(cls) -> Session:
        return IndexDB.get_session()

    @classmethod
    def commit_session(cls, session: Session) -> Session:
        return IndexDB.commit_session(session)


class ContextIndex(IndexBase):
    model: ContextModel
    session: Session

    def __init__(self) -> None:
        IndexBase.setup_index()
        self.session = self.get_session
        self.setup_context_index()

    def setup_context_index(self):
        if not (context_index := self.session.query(ContextModel).first()):
            self.session.add(ContextModel())
            if not (context_index := self.session.query(ContextModel).first()):
                raise Exception("Context index not found.")

        for db_class in DocumentDBService.REQUIRED_CLASSES:
            doc_db_name = db_class.CLASS_NAME
            existing_config = self.session.query(DocDBConfigs).filter_by(doc_db_name=doc_db_name).first()
            if not existing_config:
                db_config = db_class.ClassConfigModel().model_dump()
                new_config = DocDBConfigs(doc_db_name=doc_db_name, db_config=db_config)
                context_index.doc_db_configs.append(new_config)

        if not (domains := context_index.domains):
            default_domain = DomainModel()
            context_index.domains.append(default_domain)

        if not domains[0].sources:
            default_source = SourceModel()
            domains[0].sources.append(default_source)

        self.model = context_index
        self.session = self.commit_session(self.session)
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
    def list_of_doc_db_ui_names(self) -> list:
        return [doc_db.CLASS_UI_NAME for doc_db in DocumentDBService.REQUIRED_CLASSES]

    @property
    def list_of_doc_loading_ui_names(self) -> list:
        return [doc_db.CLASS_UI_NAME for doc_db in DocLoadingService.REQUIRED_CLASSES]

    @property
    def doc_db(self) -> DocumentDBService:
        doc_db_name = self.model.current_doc_db_name or self.model.DEFAULT_DOC_DB_NAME
        if not doc_db_name:
            doc_db_name = self.model.DEFAULT_DOC_DB_NAME

        if doc_db := self.session.query(DocDBConfigs).filter_by(doc_db_name=doc_db_name).first():
            if db_config := doc_db.db_config:
                return DocumentDBService(db_config)
        raise Exception(f"Document DB {doc_db_name} has no ClassConfigModel.")

    # def set_doc_db(self, doc_db_name: Optional[str] = None):
    #         doc_db_class = self.get_doc_db(doc_db_name)
    #         if hasattr(doc_db_class, "ClassConfigModel"):
    #             return doc_db_class.ClassConfigModel().model_dump()
    #         raise Exception(f"Document DB {doc_db_name} has no ClassConfigModel.")


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
