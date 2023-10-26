from typing import TYPE_CHECKING, Any, Optional, Sequence, Type, Union

from agents.ingest.ingest_templates import IngestTemplates
from services.document_db.document_db_service import DocumentDBService
from services.document_loading.document_loading_service import DocLoadingService
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, Relationship, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    DEFAULT_DB_NAME: str = "pinecone_database"

    # DEFAULT_LOADER_NAME: str = "generic_recursive_web_scraper"
    # enabled_doc_ingest_template_id: Mapped[int]
    # enabled_doc_ingest_name: Mapped[str]
    # enabled_doc_ingest_template_relation: Relationship["DocIngestTemplateConfigs"]
    # doc_ingest_templates: Mapped[list["DocIngestTemplateConfigs"]]

    def populate_doc_ingest_templates_configs(self):
        for template_class in IngestTemplates.AVAILABLE_TEMPLATES:
            template_name = template_class.CLASS_NAME

            existing_config = next(
                (
                    doc_ingest_template
                    for doc_ingest_template in self.doc_ingest_templates
                    if doc_ingest_template.template_name == template_name
                ),
                None,
            )
            if not existing_config:
                new_config = DocIngestTemplateConfigs(template_class)
                self.doc_ingest_templates.append(new_config)


class DocDBConfigs(Base):
    __tablename__ = "doc_dbs"
    context_id = mapped_column(Integer, ForeignKey("context_index.id"), nullable=True)
    context_model = relationship("ContextModel", back_populates="doc_dbs", foreign_keys=[context_id])

    db_name: Mapped[str] = mapped_column(String, unique=True)
    db_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


# class ChunkModel(Base):
#     pass


# class DocumentModel(Base):
#     pass


class SourceModel(Base):
    __tablename__ = "sources"

    DEFAULT_SOURCE_NAME = "default_source_name"

    name: Mapped[str] = mapped_column(String, default=DEFAULT_SOURCE_NAME)
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"))
    domain_model: Mapped["DomainModel"] = relationship("DomainModel", back_populates="sources", foreign_keys=[domain_id])

    enabled_doc_db_id = mapped_column(Integer, ForeignKey("doc_dbs.id"))
    enabled_doc_db_name = mapped_column(String)

    # enabled_doc_loader_name: Mapped[str] = mapped_column(String)
    # doc_loaders = relationship("DocLoaderConfigs", back_populates="source_model")


class DomainModel(Base):
    __tablename__ = "domains"

    DEFAULT_DOMAIN_NAME = "default_domain_name"

    name: Mapped[str] = mapped_column(String, default=DEFAULT_DOMAIN_NAME)
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"))
    context_model: Mapped["ContextModel"] = relationship("ContextModel", back_populates="domains", foreign_keys=[context_id])

    enabled_source_id = mapped_column(Integer, ForeignKey("sources.id"))
    enabled_source_relation = relationship("SourceModel", foreign_keys=[enabled_source_id])
    enabled_source_name = mapped_column(String)
    sources: Mapped[list[SourceModel]] = relationship(
        "SourceModel", back_populates="domain_model", cascade="all, delete-orphan", foreign_keys=[SourceModel.domain_id]
    )

    enabled_doc_db_id = mapped_column(Integer, ForeignKey("doc_dbs.id"))
    enabled_doc_db_name = mapped_column(String)


class ContextModel(Base):
    __tablename__ = "context_index"

    enabled_domain_id = mapped_column(Integer, ForeignKey("domains.id"))
    enabled_domain_relation = relationship("DomainModel", foreign_keys=[enabled_domain_id])
    enabled_domain_name = mapped_column(String)
    domains: Mapped[list[DomainModel]] = relationship(
        "DomainModel", back_populates="context_model", cascade="all, delete-orphan", foreign_keys=[DomainModel.context_id]
    )

    enabled_doc_db_id = mapped_column(Integer, ForeignKey("doc_dbs.id"))
    enabled_doc_db_name = mapped_column(String)
    doc_dbs: Mapped[list[DocDBConfigs]] = relationship(
        "DocDBConfigs", back_populates="context_model", foreign_keys=[DocDBConfigs.context_id]
    )

    # enabled_doc_ingest_template_id = mapped_column(Integer, ForeignKey("doc_dbs.id"))
    # enabled_doc_ingest_template_relation = relationship("DocDBConfigs", foreign_keys=[enabled_doc_ingest_template_id])
    # enabled_doc_ingest_template_name = mapped_column(String)
    # doc_ingest_templates = relationship("DocDBConfigs", back_populates="context_model")

    def enabled_doc_db(self, enabled_doc_db_id: Optional[int] = None):
        if doc_db := next((doc_db for doc_db in self.doc_dbs if doc_db.id == enabled_doc_db_id), None):
            return doc_db
        # In the case of the first run
        if doc_db := next((doc_db for doc_db in self.doc_dbs if doc_db.db_name == self.DEFAULT_DB_NAME), None):
            return doc_db
        raise Exception(f"DocDB {self.enabled_doc_db_name} not found.")


# class DocIngestTemplateConfigs(Base):
#     __tablename__ = "doc_ingest_templates"

#     context_id = mapped_column(Integer, ForeignKey("context_index.id"), nullable=True)
#     context_model = relationship("ContextModel", back_populates="doc_ingest_templates")

#     domain_id = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
#     domain_model = relationship("DomainModel", back_populates="doc_ingest_templates")

#     source_id = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
#     source_model = relationship("SourceModel", back_populates="doc_ingest_templates")

#     template_name: Mapped[str] = mapped_column(String, unique=True)

#     enabled_doc_loader_id = mapped_column(Integer, ForeignKey("doc_loaders.id"))
#     enabled_doc_loader_name = mapped_column(String)
#     enabled_doc_loader_relation = relationship("DocLoaderConfigs", foreign_keys=[enabled_doc_loader_id])


# class DocLoaderConfigs(Base):
#     __tablename__ = "doc_loaders"

#     loader_name: Mapped[str] = mapped_column(String, unique=True)
#     loader_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore
