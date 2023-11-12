import os
import typing
from typing import Any, Literal, Optional, get_args

from app.app_base import AppBase
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    __abstract__ = True


class IndexBase(AppBase):
    class_name = Literal["index"]
    CLASS_NAME: class_name = get_args(class_name)[0]
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

    @staticmethod
    def get_index_model_instance(
        list_of_instances: Any,
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Any:
        if id:
            if (
                requested_instance := next(
                    (instance for instance in list_of_instances if instance.id == id),
                    None,
                )
            ) is None:
                raise Exception(f"id {id} not found in {list_of_instances}.")
        elif name:
            if (
                requested_instance := next(
                    (instance for instance in list_of_instances if instance.name == name),
                    None,
                )
            ) is None:
                raise Exception(f"name {name} not found in {list_of_instances}.")
        else:
            raise Exception("Unexpected error: id or name should not be None at this point.")

        if requested_instance is None:
            raise Exception("Unexpected error: domain should not be None at this point.")

        return requested_instance
