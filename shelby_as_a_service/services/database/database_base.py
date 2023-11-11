from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Union

from services.service_base import ServiceBase


class DatabaseBase(ABC, ServiceBase):
    DOC_DB_REQUIRES_EMBEDDINGS: bool
    domain_name: str
    DOC_INDEX_KEY: str = "enabled_doc_db"

    @abstractmethod
    def get_index_domain_or_source_entry_count_with_provider(
        self, source_name: Optional[str] = None, domain_name: Optional[str] = None
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def query_by_terms_with_provider(
        self, search_terms: list[str] | str, domain_name: str
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_by_ids_with_provider(self, ids: list[int] | int, domain_name: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def prepare_upsert_for_vectorstore_with_provider(
        self,
        id: str,
        values: Optional[list[float]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def upsert_with_provider(
        self, entries_to_upsert: list[dict[str, Any]], domain_name: str
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def clear_existing_source_with_provider(self, source_name: str, domain_name: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def clear_existing_entries_by_id_with_provider(
        self, doc_db_ids_requiring_deletion: list[str], domain_name: str
    ) -> Any:
        raise NotImplementedError
