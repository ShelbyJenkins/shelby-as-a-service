import os
from typing import Any, Callable, Optional, Type, Union

from app.app_base import AppBase
from index.context_index_model import Base, ContextModel, DocDBConfigs, DomainModel, SourceModel
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
    def get_session(cls) -> Session:
        if cls._session_factory is None:
            raise Exception("Database not set up. Call setup_index_db first.")
        return cls._session_factory()

    def commit_session(self):
        try:
            self.session.commit()
        except:
            self.session.rollback()  # Rollback in case of error
            raise
        finally:
            self.session.close()
            return self.get_session()
