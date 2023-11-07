import os
import typing
from typing import Any, Dict, Literal, Type, Union

from app.app_base import AppBase
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    __abstract__ = True


class SqliteDatabase(AppBase):
    class_name = Literal["index"]
    CLASS_NAME: class_name = typing.get_args(class_name)[0]
    CLASS_UI_NAME: str = "Local Index - SQLite"
    _session_factory: typing.Callable[[], Session]
    session: Session
    local_index_dir: str

    @classmethod
    def setup_index(cls):
        db_path = os.path.join(cls.local_index_dir, "database.db")
        os.makedirs(cls.local_index_dir, exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        cls._session_factory = sessionmaker(bind=engine)

    @classmethod
    def get_session(cls) -> Session:
        if cls._session_factory is None:
            raise Exception("Database not set up. Call setup_index first.")
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
