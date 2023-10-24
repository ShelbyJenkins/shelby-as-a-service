from typing import Any, Optional, Type, Union

from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)

    DEFAULT_DOC_DB_NAME = "pinecone_database"
    CURRENT_DOC_LOADING_NAME = "generic_recursive_web_scraper"
    current_doc_db_name: Mapped[str] = mapped_column(String, default=DEFAULT_DOC_DB_NAME)
    current_doc_loading_name: Mapped[str] = mapped_column(String, default=CURRENT_DOC_LOADING_NAME)


# class ChunkModel(Base):
#     pass


# class DocumentModel(Base):
#     pass


class SourceModel(Base):
    __tablename__ = "sources"
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"))
    domain_model: Mapped["DomainModel"] = relationship("DomainModel", back_populates="sources")
    DEFAULT_SOURCE_NAME = "default_source_name"
    name: Mapped[str] = mapped_column(String, default="default_source_name")
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class DomainModel(Base):
    __tablename__ = "domains"
    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"))
    context_model: Mapped["ContextModel"] = relationship("ContextModel", back_populates="domains")
    sources: Mapped[list[SourceModel]] = relationship(
        "SourceModel", back_populates="domain_model", cascade="all, delete-orphan"
    )

    current_source_name: Mapped[str] = mapped_column(String, default=SourceModel.DEFAULT_SOURCE_NAME)
    DEFAULT_DOMAIN_NAME = "default_domain_name"
    name: Mapped[str] = mapped_column(String, default=DEFAULT_DOMAIN_NAME)
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ContextModel(Base):
    __tablename__ = "context_index"
    domains: Mapped[list[DomainModel]] = relationship(
        "DomainModel", back_populates="context_model", cascade="all, delete-orphan"
    )
    current_domain_name: Mapped[str] = mapped_column(String, default=DomainModel.DEFAULT_DOMAIN_NAME)

    doc_db_configs = relationship("DocDBConfigs", back_populates="context_model")


class DocDBConfigs(Base):
    __tablename__ = "doc_db_configs"
    context_id = mapped_column(Integer, ForeignKey("context_index.id"))
    context_model = relationship("ContextModel", back_populates="doc_db_configs")

    doc_db_name: Mapped[str] = mapped_column(String, unique=True)
    db_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore
