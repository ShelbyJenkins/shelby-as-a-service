from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Union

from langchain.schema import Document
from services.context_index.doc_index.context_docs import IngestDoc
from services.context_index.doc_index.doc_index_model import DomainModel, SourceModel
from services.service_base import ServiceBase


class DocLoadingBase(ABC, ServiceBase):
    DOC_INDEX_KEY: str = "enabled_doc_loader"

    def load_docs_with_provider(self, uri: str) -> Optional[list[Document]]:
        raise NotImplementedError
