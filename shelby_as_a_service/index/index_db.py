import os
from typing import Callable

from index.context_models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class IndexDB:
    _session_factory: Callable[[], Session]

    @classmethod
    def setup_index_db(cls, local_index_dir: str):
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

    @classmethod
    def commit_session(cls, session: Session) -> Session:
        try:
            session.commit()
        except:
            session.rollback()  # Rollback in case of error
            raise
        finally:
            session.close()
            return cls.get_session()
