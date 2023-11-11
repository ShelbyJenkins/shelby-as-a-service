from datetime import datetime
from typing import Any, Optional

import services.text_processing.text_utils as text_utils
from langchain.schema import Document
from pydantic import BaseModel
from services.context_index.doc_index.doc_index_model import (
    ChunkModel,
    DocumentModel,
    DomainModel,
    SourceModel,
)


class RetrievalDoc(BaseModel):
    source_name: Optional[str] = None
    domain_name: Optional[str] = None
    document_id: int
    source_id: int
    domain_id: int
    chunk_id: int
    chunk_doc_db_id: int
    title: str
    context_chunk: str
    content_token_count: int
    uri: str
    source_type: str
    date_of_last_update: datetime
    date_of_creation: datetime
    date_published: datetime


class IngestDoc(BaseModel):
    source_name: Optional[str] = None
    domain_name: Optional[str] = None
    existing_document_id: Optional[int] = None
    existing_document_model: Optional[DocumentModel] = None
    source_id: Optional[int] = None
    domain_id: Optional[int] = None
    title: str
    precleaned_content: str | dict
    precleaned_content_token_count: int = 0
    cleaned_content: Optional[str | dict] = None
    cleaned_content_token_count: int = 0
    hashed_cleaned_content: Optional[str] = None
    uri: str
    source_type: str
    date_of_last_update: datetime
    date_of_creation: datetime
    date_published: datetime

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def create_ingest_doc_from_langchain_document(
        doc: Document | dict, source: SourceModel
    ) -> "IngestDoc":
        if source.source_type == "openapi_spec":
            raise NotImplementedError

        precleaned_content = text_utils.extract_document_content(doc)

        return IngestDoc(
            source_name=source.name,
            domain_name=source.domain_model.name,
            source_id=source.id,
            domain_id=source.domain_model.id,
            title=text_utils.extract_and_clean_title(doc),
            precleaned_content=precleaned_content,
            precleaned_content_token_count=text_utils.tiktoken_len(precleaned_content),
            uri=text_utils.extract_uri(doc),
            source_type=source.source_type,
            date_of_last_update=datetime.now(),
            date_of_creation=datetime.now(),
            date_published=datetime.now(),
        )
