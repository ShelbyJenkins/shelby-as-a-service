from services.database.index_base import Base
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship


class DocLoaderModel(Base):
    __tablename__ = "doc_loaders"
    id: Mapped[int] = mapped_column(primary_key=True)

    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    domain_model = relationship("DomainModel", foreign_keys=[domain_id])
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    source_model = relationship("SourceModel", foreign_keys=[source_id])

    context_template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("index_context_templates.id"), nullable=True
    )
    context_template_model = relationship(
        "ContextTemplateModel", foreign_keys=[context_template_id]
    )

    name: Mapped[str] = mapped_column(String)
    provider_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class DocDBModel(Base):
    __tablename__ = "doc_dbs"
    id: Mapped[int] = mapped_column(primary_key=True)
    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_index_model.id"), nullable=True
    )
    context_index_model = relationship(
        "ContextIndexModel", back_populates="doc_dbs", foreign_keys=[context_id]
    )
    name: Mapped[str] = mapped_column(String, unique=True)
    provider_config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))  # type: ignore


class ContextTemplateModel(Base):
    __tablename__ = "index_context_templates"
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_index_model.id"), nullable=True
    )
    context_index_model = relationship("ContextIndexModel", foreign_keys=[context_id])

    doc_loader_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_loaders.id"), nullable=True)
    enabled_doc_loader = relationship("DocLoaderModel", foreign_keys=[doc_loader_id])
    doc_loaders: Mapped[list[DocLoaderModel]] = relationship(
        "DocLoaderModel",
        back_populates="context_template_model",
        cascade="all, delete-orphan",
        foreign_keys=[DocLoaderModel.context_template_id],
    )

    @property
    def list_of_doc_loader_names(self) -> list:
        return [doc_loader.name for doc_loader in self.doc_loaders]

    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    ennabled_doc_db = relationship("DocDBModel")

    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    name: Mapped[str] = mapped_column(String)


# class ChunkModel(Base):
#     pass


# class DocumentModel(Base):
#     pass


class SourceModel(Base):
    __tablename__ = "sources"
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

    @property
    def list_of_doc_loader_names(self) -> list:
        return [doc_loader.name for doc_loader in self.doc_loaders]

    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    ennabled_doc_db = relationship("DocDBModel")

    DEFAULT_SOURCE_NAME: str = "default_source_name"
    DEFAULT_TEMPLATE_NAME: str = "default_template_name"
    DEFAULT_SOURCE_DESCRIPTION: str = "A default source description"
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default=DEFAULT_SOURCE_DESCRIPTION)
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class DomainModel(Base):
    __tablename__ = "domains"
    id: Mapped[int] = mapped_column(primary_key=True)

    context_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("context_index_model.id"), nullable=True
    )
    context_index_model: Mapped["ContextIndexModel"] = relationship(
        "ContextIndexModel", foreign_keys=[context_id]
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
    def list_of_source_names(self) -> list:
        return [source.name for source in self.sources]

    doc_loader_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_loaders.id"), nullable=True)
    enabled_doc_loader = relationship("DocLoaderModel", foreign_keys=[doc_loader_id])
    doc_loaders: Mapped[list[DocLoaderModel]] = relationship(
        "DocLoaderModel",
        back_populates="domain_model",
        cascade="all, delete-orphan",
        foreign_keys=[DocLoaderModel.domain_id],
    )
    doc_db_id: Mapped[int] = mapped_column(Integer, ForeignKey("doc_dbs.id"), nullable=True)
    ennabled_doc_db = relationship("DocDBModel")

    DEFAULT_DOMAIN_NAME: str = "default_domain_name"
    DEFAULT_TEMPLATE_NAME: str = "default_template_name"
    DEFAULT_DOMAIN_DESCRIPTION: str = "A default domain description"
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default=DEFAULT_DOMAIN_DESCRIPTION)
    batch_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ContextIndexModel(Base):
    __tablename__ = "context_index_model"
    id: Mapped[int] = mapped_column(primary_key=True)

    current_domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), nullable=True)
    current_domain = relationship("DomainModel", foreign_keys=[current_domain_id])
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

    @property
    def list_of_doc_db_names(self) -> list:
        return [doc_db.name for doc_db in self.doc_dbs]

    index_context_templates: Mapped[list[ContextTemplateModel]] = relationship(
        "ContextTemplateModel",
        back_populates="context_index_model",
        foreign_keys=[ContextTemplateModel.context_id],
    )

    @property
    def list_of_context_template_names(self) -> list:
        return [
            index_context_template.name for index_context_template in self.index_context_templates
        ]
