from abc import ABC, abstractmethod
from typing import Union

from services.pinecone_io_pinecone_text.sparse import SparseVector


class BaseSparseEncoder(ABC):
    @abstractmethod
    def encode_documents(
        self, texts: Union[str, list[str]]
    ) -> Union[SparseVector, list[SparseVector]]:
        """
        encode documents to a sparse vector (for upsert to pinecone)

        Args:
            texts: a single or list of documents to encode as a string
        """
        pass  # pragma: no cover

    @abstractmethod
    def encode_queries(
        self, texts: Union[str, list[str]]
    ) -> Union[SparseVector, list[SparseVector]]:
        """
        encode queries to a sparse vector

        Args:
            texts: a single or list of queries to encode as a string
        """
        pass  # pragma: no cover
