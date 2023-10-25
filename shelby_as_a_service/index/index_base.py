import os
from typing import Any, Callable, Optional, Type, Union

from app.app_base import AppBase
from index.context_models import Base, ContextModel, DocDBConfigs, DocLoaderConfigs, DomainModel, SourceModel
from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class IndexBase(AppBase):
    CLASS_NAME: str = "index"
    _session_factory: Callable[[], Session]
    session: Session

    @classmethod
    def setup_index(cls):
        local_index_dir = os.path.join(cls.APP_DIR_PATH, cls.app_config.app_name, cls.CLASS_NAME)
        db_path = os.path.join(local_index_dir, "database.db")
        os.makedirs(local_index_dir, exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        cls._session_factory = sessionmaker(bind=engine)

    @classmethod
    def get_session(cls):
        if cls._session_factory is None:
            raise Exception("Database not set up. Call setup_index_db first.")
        cls.session = cls._session_factory()

    @classmethod
    def commit_session(cls):
        try:
            cls.session.commit()
        except:
            cls.session.rollback()  # Rollback in case of error
            raise
        finally:
            cls.session.close()
            cls.get_session()

    @classmethod
    def populate_doc_db_configs(cls, class_instance):
        for db_class in DocumentDBService.REQUIRED_CLASSES:
            db_name = db_class.CLASS_NAME
            existing_config = next((doc_db for doc_db in class_instance.doc_dbs if doc_db.db_name == db_name), None)

            if not existing_config:
                db_config = db_class.ClassConfigModel().model_dump()
                new_config = DocDBConfigs(db_name=db_name, db_config=db_config)
                class_instance.doc_dbs.append(new_config)

    @classmethod
    def populate_doc_loader_configs(cls, class_instance):
        for loader_class in DocLoadingService.REQUIRED_CLASSES:
            loader_name = loader_class.CLASS_NAME
            existing_config = next(
                (doc_loader for doc_loader in class_instance.doc_loaders if doc_loader.loader_name == loader_name), None
            )
            if not existing_config:
                loader_config = loader_class.ClassConfigModel().model_dump()
                new_config = DocLoaderConfigs(loader_name=loader_name, loader_config=loader_config)
                class_instance.doc_loaders.append(new_config)
