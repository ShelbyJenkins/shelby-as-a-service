from typing import TYPE_CHECKING, Any, Optional, Type, Union

from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    DEFAULT_DB_NAME: str = "pinecone_database"
    DEFAULT_LOADER_NAME: str = "generic_recursive_web_scraper"


# class ChunkModel(Base):
#     pass


# class DocumentModel(Base):
#     pass


class SourceModel(Base):
    __tablename__ = "sources"
    DEFAULT_SOURCE_NAME = "default_source_name"
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"))
    domain_model: Mapped["DomainModel"] = relationship("DomainModel", back_populates="sources")

    name: Mapped[str] = mapped_column(String, default="default_source_name")
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    enabled_doc_db_name: Mapped[str] = mapped_column(String, default=lambda: DomainModel.enabled_doc_db_name)
    enabled_doc_loader_name: Mapped[str] = mapped_column(String)
    doc_loaders = relationship("DocLoaderConfigs", back_populates="source_model")

    def __init__(self, enabled_doc_db_name: str, enabled_doc_loader_name: str):
        super().__init__()
        self.enabled_doc_db_name = enabled_doc_db_name
        self.enabled_doc_loader_name = enabled_doc_loader_name


class DomainModel(Base):
    __tablename__ = "domains"
    DEFAULT_DOMAIN_NAME = "default_domain_name"
    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"))
    context_model: Mapped["ContextModel"] = relationship("ContextModel", back_populates="domains")
    sources: Mapped[list[SourceModel]] = relationship(
        "SourceModel", back_populates="domain_model", cascade="all, delete-orphan"
    )
    current_source_name: Mapped[str] = mapped_column(String, default=SourceModel.DEFAULT_SOURCE_NAME)

    name: Mapped[str] = mapped_column(String, default=DEFAULT_DOMAIN_NAME)
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    enabled_doc_db_name: Mapped[str] = mapped_column(String)
    enabled_doc_loader_name: Mapped[str] = mapped_column(String)
    doc_loaders = relationship("DocLoaderConfigs", back_populates="domain_model")

    def __init__(self, enabled_doc_db_name: str, enabled_doc_loader_name: str):
        super().__init__()
        self.enabled_doc_db_name = enabled_doc_db_name
        self.enabled_doc_loader_name = enabled_doc_loader_name


class ContextModel(Base):
    __tablename__ = "context_index"

    domains: Mapped[list[DomainModel]] = relationship(
        "DomainModel", back_populates="context_model", cascade="all, delete-orphan"
    )
    current_domain_name: Mapped[str] = mapped_column(String, default=DomainModel.DEFAULT_DOMAIN_NAME)

    enabled_doc_db_name: Mapped[str] = mapped_column(String, default=Base.DEFAULT_DB_NAME)
    doc_dbs = relationship("DocDBConfigs", back_populates="context_model")
    enabled_doc_loader_name: Mapped[str] = mapped_column(String, default=Base.DEFAULT_LOADER_NAME)
    doc_loaders = relationship("DocLoaderConfigs", back_populates="context_model")


class DocDBConfigs(Base):
    __tablename__ = "doc_dbs"
    context_id = mapped_column(Integer, ForeignKey("context_index.id"))
    context_model = relationship("ContextModel", back_populates="doc_dbs")

    db_name: Mapped[str] = mapped_column(String, unique=True)
    db_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class DocLoaderConfigs(Base):
    __tablename__ = "doc_loaders"

    context_id = mapped_column(Integer, ForeignKey("context_index.id"), nullable=True)
    context_model = relationship("ContextModel", back_populates="doc_loaders")

    domain_id = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model = relationship("DomainModel", back_populates="doc_loaders")

    source_id = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source_model = relationship("SourceModel", back_populates="doc_loaders")

    loader_name: Mapped[str] = mapped_column(String, unique=True)
    loader_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore
