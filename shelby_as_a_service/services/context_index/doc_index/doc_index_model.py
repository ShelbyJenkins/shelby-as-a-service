from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, get_args

from services.context_index.index_base import Base
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship


class DocIngestProcessorModel(Base):
    class_name = Literal["doc_ingest_processors"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    id: Mapped[int] = mapped_column(primary_key=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model = relationship("DomainModel", foreign_keys=[domain_id])
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source_model = relationship("SourceModel", foreign_keys=[source_id])

    DEFAULT_PROVIDER_NAME: str = "process_ingest_documents"
    name: Mapped[str] = mapped_column(String)
    config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class DocLoaderModel(Base):
    class_name = Literal["doc_loaders"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    id: Mapped[int] = mapped_column(primary_key=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model = relationship("DomainModel", foreign_keys=[domain_id])
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source_model = relationship("SourceModel", foreign_keys=[source_id])

    DEFAULT_PROVIDER_NAME: str = "generic_recursive_web_scraper"
    name: Mapped[str] = mapped_column(String)
    config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class DocEmbeddingModel(Base):
    class_name = Literal["doc_embedders"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    doc_db_model: Mapped["DocDBModel"] = relationship("DocDBModel", foreign_keys=[doc_db_id])

    DEFAULT_PROVIDER_NAME: str = "openai_embedding"
    name: Mapped[str] = mapped_column(String, unique=True)
    config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class DocDBModel(Base):
    class_name = Literal["doc_dbs"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    id: Mapped[int] = mapped_column(primary_key=True)
    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_index_model.id"), nullable=True
    )
    doc_index_model = relationship(
        "DocIndexModel", back_populates="doc_dbs", foreign_keys=[context_id]
    )

    doc_embedder_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_embedders.id"), nullable=True
    )
    enabled_doc_embedder = relationship("DocLoaderModel", foreign_keys=[doc_embedder_id])
    doc_embedders: Mapped[list[DocEmbeddingModel]] = relationship(
        "DocEmbeddingModel",
        back_populates="doc_db_model",
        cascade="all, delete-orphan",
        foreign_keys=[DocEmbeddingModel.doc_db_id],
    )

    DEFAULT_PROVIDER_NAME: str = "pinecone_database"
    name: Mapped[str] = mapped_column(String, unique=True)
    config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class DocIndexTemplateModel(Base):
    class_name = Literal["documents"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    __tablename__ = "doc_index_templates"
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_index_model.id"), nullable=True
    )
    doc_index_model = relationship("DocIndexModel", foreign_keys=[context_id])

    enabled_doc_loader_name: Mapped[str] = mapped_column(String)
    enabled_doc_loader_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore

    enabled_doc_ingest_processor_name: Mapped[str] = mapped_column(String)
    enabled_doc_ingest_processor_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore

    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    enabled_doc_db = relationship("DocDBModel")

    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    name: Mapped[str] = mapped_column(String)


class ChunkModel(Base):
    class_name = Literal["documents"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=True)
    document_model: Mapped["DocumentModel"] = relationship(
        "DocumentModel", foreign_keys=[document_id]
    )

    context_chunk: Mapped[str] = mapped_column(String, nullable=True)
    chunk_embedding: Mapped[list[float]] = mapped_column(PickleType, nullable=True)
    chunk_doc_db_id: Mapped[str] = mapped_column(String, nullable=True)

    def prepare_upsert_metadata(self) -> dict:
        metadata = {
            "domain_name": self.document_model.domain_model.name,
            "source_name": self.document_model.source_model.name,
            "context_chunk": self.context_chunk,
            "document_id": self.document_model.id,
            "title": self.document_model.title,
            "uri": self.document_model.uri,
            "source_type": self.document_model.source_type,
            "date_of_creation": self.document_model.date_of_creation,
        }
        return metadata


class DocumentModel(Base):
    class_name = Literal["documents"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source_model: Mapped["SourceModel"] = relationship("SourceModel", foreign_keys=[source_id])
    domain_model: Mapped["DomainModel"] = relationship(
        "DomainModel",
        secondary="sources",
        primaryjoin="DocumentModel.source_id==SourceModel.id",
        secondaryjoin="SourceModel.domain_id==DomainModel.id",
        viewonly=True,
        uselist=False,  # Since each document is related to one domain through its source
    )
    context_chunks: Mapped[list[ChunkModel]] = relationship(
        "ChunkModel",
        back_populates="document_model",
        cascade="all, delete-orphan",
        foreign_keys=[ChunkModel.document_id],
    )
    cleaned_content: Mapped[str] = mapped_column(String, nullable=True)
    hashed_cleaned_content: Mapped[str] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    uri: Mapped[str] = mapped_column(String, nullable=True)
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    source_type: Mapped[str] = mapped_column(String, nullable=True)
    date_published: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    date_of_creation: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    date_of_last_update: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SourceModel(Base):
    class_name = Literal["sources"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    id: Mapped[int] = mapped_column(primary_key=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model: Mapped["DomainModel"] = relationship("DomainModel", foreign_keys=[domain_id])

    doc_loader_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_loaders.id"), nullable=True)
    enabled_doc_loader = relationship("DocLoaderModel", foreign_keys=[doc_loader_id])
    doc_loaders: Mapped[list[DocLoaderModel]] = relationship(
        "DocLoaderModel",
        back_populates="source_model",
        cascade="all, delete-orphan",
        foreign_keys=[DocLoaderModel.source_id],
    )

    doc_ingest_processor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_ingest_processors.id"), nullable=True
    )
    enabled_doc_ingest_processor = relationship(
        "DocIngestProcessorModel", foreign_keys=[doc_ingest_processor_id]
    )
    doc_ingest_processors: Mapped[list[DocIngestProcessorModel]] = relationship(
        "DocIngestProcessorModel",
        back_populates="source_model",
        cascade="all, delete-orphan",
        foreign_keys=[DocIngestProcessorModel.source_id],
    )

    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    enabled_doc_db = relationship("DocDBModel")

    DEFAULT_NAME: str = "default_source_name"
    DEFAULT_TEMPLATE_NAME: str = "default_template_name"
    DEFAULT_DESCRIPTION: str = "A default source description"
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default=DEFAULT_DESCRIPTION)
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    source_uri: Mapped[str] = mapped_column(String, nullable=True)
    source_type: Mapped[str] = mapped_column(String, nullable=True)

    documents: Mapped[list[DocumentModel]] = relationship(
        "DocumentModel",
        back_populates="source_model",
        cascade="all, delete-orphan",
        foreign_keys=[DocumentModel.source_id],
    )
    date_of_last_successful_update: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class DomainModel(Base):
    class_name = Literal["domains"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_index_model.id"), nullable=True
    )
    doc_index_model: Mapped["DocIndexModel"] = relationship(
        "DocIndexModel", foreign_keys=[context_id]
    )

    current_source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    current_source = relationship("SourceModel", foreign_keys=[current_source_id])
    sources: Mapped[list[SourceModel]] = relationship(
        "SourceModel",
        back_populates="domain_model",
        cascade="all, delete-orphan",
        foreign_keys=[SourceModel.domain_id],
    )

    @property
    def source_names(self) -> list:
        return [source.name for source in self.sources]

    doc_ingest_processor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doc_ingest_processors.id"), nullable=True
    )
    enabled_doc_ingest_processor = relationship(
        "DocIngestProcessorModel", foreign_keys=[doc_ingest_processor_id]
    )
    doc_ingest_processors: Mapped[list[DocIngestProcessorModel]] = relationship(
        "DocIngestProcessorModel",
        back_populates="domain_model",
        cascade="all, delete-orphan",
        foreign_keys=[DocIngestProcessorModel.domain_id],
    )

    doc_loader_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_loaders.id"), nullable=True)
    enabled_doc_loader = relationship("DocLoaderModel", foreign_keys=[doc_loader_id])
    doc_loaders: Mapped[list[DocLoaderModel]] = relationship(
        "DocLoaderModel",
        back_populates="domain_model",
        cascade="all, delete-orphan",
        foreign_keys=[DocLoaderModel.domain_id],
    )

    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    enabled_doc_db = relationship("DocDBModel")

    DEFAULT_NAME: str = "default_domain_name"
    DEFAULT_TEMPLATE_NAME: str = "default_template_name"
    DEFAULT_DESCRIPTION: str = "A default domain description"
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(String, default=DEFAULT_DESCRIPTION)
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    documents: Mapped[list[DocumentModel]] = relationship(
        "DocumentModel",
        secondary="sources",
        primaryjoin="DomainModel.id==SourceModel.domain_id",
        secondaryjoin="SourceModel.id==DocumentModel.source_id",
        viewonly=True,
    )


class DocIndexModel(Base):
    class_name = Literal["doc_index_model"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    __tablename__ = CLASS_NAME
    id: Mapped[int] = mapped_column(primary_key=True)

    current_domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    current_domain = relationship("DomainModel", foreign_keys=[current_domain_id])
    domains: Mapped[list[DomainModel]] = relationship(
        "DomainModel",
        back_populates="doc_index_model",
        cascade="all, delete-orphan",
        foreign_keys=[DomainModel.context_id],
    )

    doc_dbs: Mapped[list[DocDBModel]] = relationship(
        "DocDBModel",
        back_populates="doc_index_model",
        foreign_keys="DocDBModel.context_id",
    )

    @property
    def list_of_doc_db_names(self) -> list:
        return [doc_db.name for doc_db in self.doc_dbs]

    doc_index_templates: Mapped[list[DocIndexTemplateModel]] = relationship(
        "DocIndexTemplateModel",
        back_populates="doc_index_model",
        foreign_keys=[DocIndexTemplateModel.context_id],
    )

    @property
    def list_of_doc_index_template_names(self) -> list:
        return [doc_index_template.name for doc_index_template in self.doc_index_templates]
