from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel
from services.service_base import ServiceBase


class ClassConfigModel(BaseModel):
    index_env: str
    index_name: str
    vectorstore_dimension: int
    upsert_batch_size: int
    vectorstore_metric: str
    vectorstore_pod_type: str
    enabled_doc_embedder_name: str
    enabled_doc_embedder_config: dict[str, Any]
    retrieve_n_docs: int
    indexed_metadata: list[str]


class DatabaseBase(ABC, ServiceBase):
    DOC_DB_REQUIRES_EMBEDDINGS: bool
    domain_name: str
    DOC_INDEX_KEY: str = "enabled_doc_db"

    config: ClassConfigModel

    def get_index_domain_or_source_entry_count_with_provider(
        self, source_name: Optional[str] = None, domain_name: Optional[str] = None
    ) -> int:
        raise NotImplementedError

    def query_by_terms_with_provider(
        self,
        search_terms: list[float] | str,
        domain_name: str,
        retrieve_n_docs: Optional[int] = None,
    ) -> list[dict]:
        raise NotImplementedError

    def fetch_by_ids_with_provider(
        self,
        ids: list[str],
        domain_name: str,
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    def prepare_upsert_for_vectorstore_with_provider(
        self,
        id: str,
        values: Optional[list[float]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    def upsert_with_provider(
        self, entries_to_upsert: list[dict[str, Any]], domain_name: str
    ) -> Any:
        raise NotImplementedError

    def clear_existing_source_with_provider(self, source_name: str, domain_name: str) -> Any:
        raise NotImplementedError

    def clear_existing_entries_by_id_with_provider(
        self, doc_db_ids_requiring_deletion: list[str], domain_name: str
    ) -> Any:
        raise NotImplementedError
