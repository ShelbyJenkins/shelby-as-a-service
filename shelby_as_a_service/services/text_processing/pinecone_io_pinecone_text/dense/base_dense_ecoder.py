from abc import ABC, abstractmethod
from typing import Union


class BaseDenseEncoder(ABC):
    @abstractmethod
    def encode_documents(
        self, texts: Union[str, list[str]]
    ) -> Union[list[float], list[list[float]]]:
        """
        encode documents to a dense vector (for upsert to pinecone)

        Args:
            texts: a single or list of documents to encode as a string
        """
        pass  # pragma: no cover

    @abstractmethod
    def encode_queries(self, texts: Union[str, list[str]]) -> Union[list[float], list[list[float]]]:
        """
        encode queries to a dense vector

        Args:
            texts: a single or list of queries to encode as a string
        """
        pass  # pragma: no cover
