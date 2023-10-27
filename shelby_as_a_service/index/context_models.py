from typing import TYPE_CHECKING, Any, Optional, Sequence, Type, Union

from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, Relationship, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    DEFAULT_DB_NAME: str = "pinecone_database"
    DEFAULT_TEMPLATE_NAME: str = "generic_recursive_web_scraper"


class DocDBConfigs(Base):
    __tablename__ = "doc_dbs"
    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"), nullable=True)
    context_model: Relationship[Any] = relationship("ContextModel", back_populates="doc_dbs", foreign_keys=[context_id])

    db_name: Mapped[str] = mapped_column(String, unique=True)
    db_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class DocIngestTemplateConfigs(Base):
    __tablename__ = "doc_ingest_templates"

    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"), nullable=True)
    context_model: Relationship[Any] = relationship(
        "ContextModel", back_populates="doc_ingest_templates", foreign_keys=[context_id]
    )

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model: Relationship[Any] = relationship(
        "DomainModel", back_populates="doc_ingest_templates", foreign_keys=[domain_id]
    )

    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source_model: Relationship[Any] = relationship(
        "SourceModel", back_populates="doc_ingest_templates", foreign_keys=[source_id]
    )

    template_name: Mapped[str] = mapped_column(String)
    loader_name: Mapped[str] = mapped_column(String)
    loader_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


# class ChunkModel(Base):
#     pass


# class DocumentModel(Base):
#     pass


class SourceModel(Base):
    __tablename__ = "sources"

    DEFAULT_SOURCE_NAME: str = "default_source_name"

    name: Mapped[str] = mapped_column(String, default=DEFAULT_SOURCE_NAME)
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"))
    domain_model: Mapped["DomainModel"] = relationship("DomainModel", back_populates="sources", foreign_keys=[domain_id])

    enabled_doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"))
    enabled_doc_db_name: Mapped[str] = mapped_column(String)

    enabled_doc_ingest_template_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_ingest_templates.id"))
    enabled_doc_ingest_template_name: Mapped[str] = mapped_column(String)
    enabled_doc_ingest_template_relation: Relationship[DocIngestTemplateConfigs] = relationship(
        "DocIngestTemplateConfigs", foreign_keys=[enabled_doc_ingest_template_id]
    )
    doc_ingest_templates: Mapped[list[DocIngestTemplateConfigs]] = relationship(
        "DocIngestTemplateConfigs", back_populates="source_model", foreign_keys=[DocIngestTemplateConfigs.source_id]
    )


class DomainModel(Base):
    __tablename__ = "domains"

    DEFAULT_DOMAIN_NAME: str = "default_domain_name"

    name: Mapped[str] = mapped_column(String, default=DEFAULT_DOMAIN_NAME)
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"))
    context_model: Mapped["ContextModel"] = relationship("ContextModel", back_populates="domains", foreign_keys=[context_id])

    enabled_source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"))
    enabled_source_relation = relationship("SourceModel", foreign_keys=[enabled_source_id])
    enabled_source_name: Mapped[str] = mapped_column(String)
    sources: Mapped[list[SourceModel]] = relationship(
        "SourceModel", back_populates="domain_model", cascade="all, delete-orphan", foreign_keys=[SourceModel.domain_id]
    )

    enabled_doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"))
    enabled_doc_db_name: Mapped[str] = mapped_column(String)

    enabled_doc_ingest_template_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_ingest_templates.id"))
    enabled_doc_ingest_template_name: Mapped[str] = mapped_column(String)
    enabled_doc_ingest_template_relation: Relationship[DocIngestTemplateConfigs] = relationship(
        "DocIngestTemplateConfigs", foreign_keys=[enabled_doc_ingest_template_id]
    )
    doc_ingest_templates: Mapped[list[DocIngestTemplateConfigs]] = relationship(
        "DocIngestTemplateConfigs", back_populates="domain_model", foreign_keys=[DocIngestTemplateConfigs.domain_id]
    )


class ContextModel(Base):
    __tablename__ = "context_index"

    enabled_domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"))
    enabled_domain_relation: Relationship[DomainModel] = relationship("DomainModel", foreign_keys=[enabled_domain_id])
    enabled_domain_name: Mapped[str] = mapped_column(String)
    domains: Mapped[list[DomainModel]] = relationship(
        "DomainModel", back_populates="context_model", cascade="all, delete-orphan", foreign_keys=[DomainModel.context_id]
    )

    enabled_doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"))
    enabled_doc_db_name: Mapped[str] = mapped_column(String)
    doc_dbs: Relationship[Any] = relationship("DocDBConfigs", back_populates="context_model")

    # Used for all templates in app
    enabled_doc_ingest_template_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_ingest_templates.id"))
    enabled_doc_ingest_template_name: Mapped[str] = mapped_column(String)
    enabled_doc_ingest_template_relation: Relationship[DocIngestTemplateConfigs] = relationship(
        "DocIngestTemplateConfigs", foreign_keys=[enabled_doc_ingest_template_id], uselist=False, lazy="select"
    )
    doc_ingest_templates: Mapped[list[DocIngestTemplateConfigs]] = relationship(
        "DocIngestTemplateConfigs", back_populates="context_model", foreign_keys=[DocIngestTemplateConfigs.context_id]
    )
