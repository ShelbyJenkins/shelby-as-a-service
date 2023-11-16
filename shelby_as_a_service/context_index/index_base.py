import os
import typing
from typing import Any, Literal, Optional, Type, get_args

from app.app_base import AppBase, LoggerWrapper
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    __abstract__ = True


class IndexBase(AppBase):
    class_name = Literal["index"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Local Index - SQLite"
    _session_factory: typing.Callable[[], Session]
    _write_session_factory: typing.Callable[[], Session]
    session: Session
    local_index_dir: str
    logger_wrapper = LoggerWrapper

    @classmethod
    def setup_index(cls):
        db_path = os.path.join(cls.local_index_dir, "database.db")
        os.makedirs(cls.local_index_dir, exist_ok=True)
        IndexBase.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(cls.engine)
        IndexBase._session_factory = sessionmaker(bind=cls.engine, expire_on_commit=False)
        IndexBase._write_session_factory = sessionmaker(bind=cls.engine)

    @classmethod
    def indexbase_open_session(cls, obj: Optional[Any] = None) -> Session:
        if IndexBase._session_factory is None:
            raise Exception("Database not set up. Call IndexBase.setup_index first.")
        session = IndexBase._session_factory()
        if obj is not None:
            session.add(obj)
        return session

    @classmethod
    def indexbase_close_session(cls, session: Session):
        if session.is_active:
            session.commit()
        elif session.dirty:
            cls.log.info("Session was dirty. Rolling back.")
            session.rollback()
        session.expunge_all()
        session.close()

    @classmethod
    def indexbase_open_write_session(cls, obj) -> Session:
        if IndexBase._write_session_factory is None:
            raise Exception("Database not set up. Call IndexBase.setup_index first.")
        write_session = IndexBase._write_session_factory()
        write_session.add(obj)
        return write_session

    @classmethod
    def indexbase_close_write_session(cls, write_session: Optional[Session] = None):
        if write_session is None:
            cls.log.info("No write session to close.")
            return
        cls.indexbase_close_session(write_session)

    @classmethod
    def indexbase_commit_session(cls, session: Optional[Session] = None):
        if session is None:
            cls.log.info("No session to commit.")
            return
        try:
            session.commit()
        except:
            session.rollback()
            cls.log.info("Session was dirty. Rolling back.")

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

    @staticmethod
    def get_requested_class(
        requested_class: str, available_classes: list[Type["IndexBase"]]
    ) -> Any:
        for available_class in available_classes:
            if (
                available_class.CLASS_NAME == requested_class
                or available_class.CLASS_UI_NAME == requested_class
            ):
                return available_class
        raise ValueError(f"Requested class {requested_class} not found in {available_classes}")
