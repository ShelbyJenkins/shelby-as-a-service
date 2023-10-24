from typing import Any, Optional, Type, Union

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ContextIndex(Base):
    __tablename__ = "context_indexes"

    id = Column(Integer, primary_key=True)
    # Relationship indicating one ContextIndex can have multiple DataDomain entries
    data_domains = relationship("DataDomain", back_populates="context_index", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "data_domains": [domain.to_dict() for domain in self.data_domains]}


class DataDomain(Base):
    __tablename__ = "data_domains"

    id = Column(Integer, primary_key=True)
    name = Column(String, default="default_data_domain")
    description = Column(String, default="A default description")
    batch_update_enabled = Column(Boolean, default=True)

    context_id = Column(Integer, ForeignKey("context_indexes.id"))
    context_index = relationship("ContextIndex", back_populates="data_domains")

    # Relationship with DataSource
    data_sources = relationship("DataSource", back_populates="data_domain", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "batch_update_enabled": self.batch_update_enabled,
            "data_sources": [source.to_dict() for source in self.data_sources],
        }


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String, default="default_data_source")
    description = Column(String, default="A default description")
    batch_update_enabled = Column(Boolean, default=True)

    domain_id = Column(Integer, ForeignKey("data_domains.id"))
    data_domain = relationship("DataDomain", back_populates="data_sources")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "batch_update_enabled": self.batch_update_enabled,
        }


class ChunkModel(Base):
    pass


class DocumentModel(Base):
    pass
