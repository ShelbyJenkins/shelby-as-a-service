import os
from typing import Any, Callable, Optional, Type, Union

from app.app_base import AppBase
from index.context_models import Base, ContextModel, DocDBConfigs, DomainModel, SourceModel
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
