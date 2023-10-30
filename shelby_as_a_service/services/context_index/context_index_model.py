from services.database.index_base import Base
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship


class DocDBModel(Base):
    __tablename__ = "doc_dbs"
    id: Mapped[int] = mapped_column(primary_key=True)
    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_index_model.id"), nullable=True
    )
    context_index_model = relationship(
        "ContextIndexModel", back_populates="doc_dbs", foreign_keys=[context_id]
    )
    database_provider_name: Mapped[str] = mapped_column(String, unique=True)
    db_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class ContextTemplateModel(Base):
    __tablename__ = "index_context_templates"
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_index_model.id"), nullable=True
    )
    context_index_model = relationship("ContextIndexModel", foreign_keys=[context_id])

    context_template_name: Mapped[str] = mapped_column(String)
    doc_loading_provider_name: Mapped[str] = mapped_column(String)
    doc_loading_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore
    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    doc_db = relationship("DocDBModel")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ContextConfigModel(Base):
    __tablename__ = "context_configs"
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_index_model.id"), nullable=True
    )
    context_index_model = relationship("ContextIndexModel", foreign_keys=[context_id])

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model = relationship("DomainModel", foreign_keys=[domain_id])

    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source_model = relationship("SourceModel", foreign_keys=[source_id])

    context_config_name: Mapped[str] = mapped_column(String)
    doc_loading_provider_name: Mapped[str] = mapped_column(String)
    doc_loading_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore
    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    doc_db = relationship("DocDBModel")
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


# class ChunkModel(Base):
#     pass


# class DocumentModel(Base):
#     pass


class SourceModel(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model: Mapped["DomainModel"] = relationship("DomainModel", foreign_keys=[domain_id])

    context_config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_configs.id"), nullable=True
    )
    context_config = relationship("ContextConfigModel", foreign_keys=[context_config_id])
    context_configs: Mapped[list[ContextConfigModel]] = relationship(
        "ContextConfigModel",
        back_populates="source_model",
        foreign_keys=[ContextConfigModel.source_id],
    )

    DEFAULT_SOURCE_NAME: str = "default_source_name"
    DEFAULT_TEMPLATE_NAME: str = "default_template_name"
    DEFAULT_SOURCE_DESCRIPTION: str = "A default source description"
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default=DEFAULT_SOURCE_DESCRIPTION)


class DomainModel(Base):
    __tablename__ = "domains"
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_index_model.id"), nullable=True
    )
    context_index_model: Mapped["ContextIndexModel"] = relationship(
        "ContextIndexModel", foreign_keys=[context_id]
    )

    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source = relationship("SourceModel", foreign_keys=[source_id])
    sources: Mapped[list[SourceModel]] = relationship(
        "SourceModel",
        back_populates="domain_model",
        cascade="all, delete-orphan",
        foreign_keys=[SourceModel.domain_id],
    )

    context_config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_configs.id"), nullable=True
    )
    context_config = relationship("ContextConfigModel", foreign_keys=[context_config_id])
    context_configs: Mapped[list[ContextConfigModel]] = relationship(
        "ContextConfigModel",
        back_populates="domain_model",
        foreign_keys=[ContextConfigModel.domain_id],
    )

    DEFAULT_DOMAIN_NAME: str = "default_domain_name"
    DEFAULT_TEMPLATE_NAME: str = "default_template_name"
    DEFAULT_DOMAIN_DESCRIPTION: str = "A default domain description"
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default=DEFAULT_DOMAIN_DESCRIPTION)


class ContextIndexModel(Base):
    __tablename__ = "context_index_model"
    id: Mapped[int] = mapped_column(primary_key=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain = relationship("DomainModel", foreign_keys=[domain_id])
    domains: Mapped[list[DomainModel]] = relationship(
        "DomainModel",
        back_populates="context_index_model",
        cascade="all, delete-orphan",
        foreign_keys=[DomainModel.context_id],
    )

    doc_dbs: Mapped[list[DocDBModel]] = relationship(
        "DocDBModel",
        back_populates="context_index_model",
        foreign_keys="DocDBModel.context_id",
    )

    index_context_templates: Mapped[list[ContextTemplateModel]] = relationship(
        "ContextTemplateModel",
        back_populates="context_index_model",
        foreign_keys=[ContextTemplateModel.context_id],
    )
