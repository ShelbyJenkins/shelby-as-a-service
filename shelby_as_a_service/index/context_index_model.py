from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    __abstract__ = True

    DEFAULT_DB_NAME: str = "pinecone_database"
    DEFAULT_INGEST_TEMPLATE_NAME: str = "Generic Recusive Web Scraper"


class DocDBConfigs(Base):
    __tablename__ = "doc_dbs"
    id: Mapped[int] = mapped_column(primary_key=True)
    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"), nullable=True)
    context_model = relationship(
        "ContextModel", back_populates="doc_dbs", foreign_keys=[context_id]
    )
    db_name: Mapped[str] = mapped_column(String, unique=True)
    db_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class DocIngestTemplateConfigs(Base):
    __tablename__ = "doc_ingest_templates"
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"), nullable=True)
    context_model = relationship("ContextModel", foreign_keys=[context_id])

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model = relationship("DomainModel", foreign_keys=[domain_id])

    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source_model = relationship("SourceModel", foreign_keys=[source_id])

    ingest_template_name: Mapped[str] = mapped_column(String)
    loader_name: Mapped[str] = mapped_column(String)
    loader_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


# class ChunkModel(Base):
#     pass


# class DocumentModel(Base):
#     pass


class SourceModel(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model: Mapped["DomainModel"] = relationship("DomainModel", foreign_keys=[domain_id])

    enabled_doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    enabled_doc_db = relationship("DocDBConfigs")

    enabled_doc_ingest_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_ingest_templates.id"), nullable=True
    )
    enabled_doc_ingest_template = relationship(
        "DocIngestTemplateConfigs", foreign_keys=[enabled_doc_ingest_template_id]
    )
    doc_ingest_templates: Mapped[list[DocIngestTemplateConfigs]] = relationship(
        "DocIngestTemplateConfigs",
        back_populates="source_model",
        foreign_keys=[DocIngestTemplateConfigs.source_id],
    )

    DEFAULT_SOURCE_NAME: str = "default_source_name"
    name: Mapped[str] = mapped_column(String, default=DEFAULT_SOURCE_NAME)
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class DomainModel(Base):
    __tablename__ = "domains"
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(Integer, ForeignKey("context_index.id"), nullable=True)
    context_model: Mapped["ContextModel"] = relationship("ContextModel", foreign_keys=[context_id])

    enabled_source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    enabled_source = relationship("SourceModel", foreign_keys=[enabled_source_id])
    sources: Mapped[list[SourceModel]] = relationship(
        "SourceModel",
        back_populates="domain_model",
        cascade="all, delete-orphan",
        foreign_keys=[SourceModel.domain_id],
    )

    enabled_doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    enabled_doc_db = relationship("DocDBConfigs")

    enabled_doc_ingest_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_ingest_templates.id"), nullable=True
    )
    enabled_doc_ingest_template = relationship(
        "DocIngestTemplateConfigs", foreign_keys=[enabled_doc_ingest_template_id]
    )
    doc_ingest_templates: Mapped[list[DocIngestTemplateConfigs]] = relationship(
        "DocIngestTemplateConfigs",
        back_populates="domain_model",
        foreign_keys=[DocIngestTemplateConfigs.domain_id],
    )

    DEFAULT_DOMAIN_NAME: str = "default_domain_name"
    name: Mapped[str] = mapped_column(String, default=DEFAULT_DOMAIN_NAME)
    description: Mapped[str] = mapped_column(String, default="A default description")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ContextModel(Base):
    __tablename__ = "context_index"
    id: Mapped[int] = mapped_column(primary_key=True)

    enabled_domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    enabled_domain = relationship("DomainModel", foreign_keys=[enabled_domain_id])
    domains: Mapped[list[DomainModel]] = relationship(
        "DomainModel",
        back_populates="context_model",
        cascade="all, delete-orphan",
        foreign_keys=[DomainModel.context_id],
    )

    enabled_doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    enabled_doc_db = relationship("DocDBConfigs", foreign_keys=[enabled_doc_db_id])
    doc_dbs: Mapped[list[DocDBConfigs]] = relationship(
        "DocDBConfigs",
        back_populates="context_model",
        foreign_keys="DocDBConfigs.context_id",
    )

    # Used for all templates in app
    enabled_doc_ingest_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_ingest_templates.id"), nullable=True
    )
    enabled_doc_ingest_template = relationship(
        "DocIngestTemplateConfigs", foreign_keys=[enabled_doc_ingest_template_id]
    )
    doc_ingest_templates: Mapped[list[DocIngestTemplateConfigs]] = relationship(
        "DocIngestTemplateConfigs",
        back_populates="context_model",
        foreign_keys=[DocIngestTemplateConfigs.context_id],
    )
