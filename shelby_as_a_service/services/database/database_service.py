from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Union

import interfaces.webui.gradio_helpers as GradioHelpers
from services.context_index.doc_index.context_docs import IngestDoc
from services.context_index.doc_index.doc_index_model import ChunkModel, DomainModel, SourceModel
from services.embedding.embedding_service import EmbeddingService
from services.service_base import ServiceBase

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class DatabaseService(ABC, ServiceBase):
    CLASS_NAME: str = "database_service"
    CONTEXT_INDEX_PROVIDER_KEY: str = "enabled_doc_db"
    CLASS_UI_NAME: str = "Document Databases"
    AVAILABLE_PROVIDERS: list[Type] = AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES
    DOC_DB_REQUIRES_EMBEDDINGS: bool
    domain_name: str

    @classmethod
    def load_service_from_context_index(
        cls, domain_or_source: DomainModel | SourceModel
    ) -> "DatabaseService":
        instance: DatabaseService = cls.get_instance_from_context_index(
            domain_or_source=domain_or_source
        )
        setattr(instance, "domain_name", instance.domain.name)
        return instance

    def upsert_documents_from_context_index_source(self, upsert_docs: list[IngestDoc]):
        self.check_for_source
        current_entry_count = self.get_index_domain_or_source_entry_count_with_provider(
            source_name=self.source.name
        )
        current_entry_count += 1
        chunks_to_upsert: list[ChunkModel] = []
        for doc in upsert_docs:
            if not doc.existing_document_model:
                raise ValueError(f"No existing_document_model for doc {doc.title}")
            if not doc.existing_document_model.context_chunks:
                raise ValueError(f"No context_chunks for doc {doc.title}")
            for i, chunk in enumerate(doc.existing_document_model.context_chunks):
                chunk_doc_db_id = f"id-{self.source.name}-{i + current_entry_count}"
                chunk.chunk_doc_db_id = chunk_doc_db_id
                chunks_to_upsert.append(chunk)

        entries_to_upsert = []
        if self.DOC_DB_REQUIRES_EMBEDDINGS:
            EmbeddingService.load_service_from_context_index(
                domain_or_source=self.source
            ).get_document_embeddings_for_chunks_to_upsert(chunks_to_upsert=chunks_to_upsert)
            for chunk in chunks_to_upsert:
                metadata = chunk.prepare_upsert_metadata()
                entries_to_upsert.append(
                    self.prepare_upsert_for_vectorstore_with_provider(
                        id=chunk.chunk_doc_db_id, values=chunk.chunk_embedding, metadata=metadata
                    )
                )
        else:
            raise NotImplementedError

        self.upsert(entries_to_upsert=entries_to_upsert, domain_name=self.domain_name)

    def clear_existing_entries_by_id(
        self,
        domain_name: str,
        doc_db_ids_requiring_deletion: list[str],
        source_name: Optional[str] = None,
    ):
        existing_entry_count = self.get_index_domain_or_source_entry_count_with_provider(
            source_name=source_name, domain_name=domain_name
        )

        response = self.clear_existing_entries_by_id_with_provider(
            doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
            domain_name=domain_name,
        )
        post_delete_entry_count = self.get_index_domain_or_source_entry_count_with_provider(
            source_name=source_name, domain_name=domain_name
        )
        if existing_entry_count - post_delete_entry_count != len(doc_db_ids_requiring_deletion):
            raise ValueError(
                f"Deleted {len(doc_db_ids_requiring_deletion)} entries but expected to delete {existing_entry_count - post_delete_entry_count}.\n Response: {response}"
            )
        else:
            self.log.info(
                f"Deleted {len(doc_db_ids_requiring_deletion)} entries from {self.CLASS_NAME}.\n Response: {response}"
            )

    def upsert(
        self,
        domain_name: str,
        entries_to_upsert: list[dict[str, Any]],
    ):
        current_entry_count = self.get_index_domain_or_source_entry_count_with_provider(
            source_name=self.source.name
        )
        self.log.info(f"Upserting {len(entries_to_upsert)} entries to {self.CLASS_NAME}")

        response = self.upsert_with_provider(
            entries_to_upsert=entries_to_upsert, domain_name=domain_name
        )

        post_upsert_entry_count = self.get_index_domain_or_source_entry_count_with_provider(
            source_name=self.source.name
        )
        if post_upsert_entry_count - current_entry_count != len(entries_to_upsert):
            raise ValueError(
                f"Upserted {len(entries_to_upsert)} entries but expected to upsert {post_upsert_entry_count - current_entry_count}.\n Response: {response}"
            )
        self.log.info(
            f"Successfully upserted {len(entries_to_upsert)} entries to {self.CLASS_NAME}.\n Response: {response}"
        )

    def query_by_terms(self, domain_name: str, search_terms: list[str] | str) -> list[dict]:
        if isinstance(search_terms, str):
            search_terms = [search_terms]
        retrieved_docs = []
        for term in search_terms:
            docs = self.query_by_terms_with_provider(search_terms=term, domain_name=domain_name)
            if docs:
                retrieved_docs.extend(docs)
            else:
                self.log.info(f"No documents found for {term}")
        return retrieved_docs

    def fetch_by_ids(self, domain_name: str, ids: list[int] | int) -> list[dict]:
        if isinstance(ids, int):
            ids = [ids]

        docs = self.fetch_by_ids_with_provider(ids=ids, domain_name=domain_name)
        if not docs:
            self.log.info(f"No documents found for {id}")
        return docs

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

    @classmethod
    def create_service_ui_components(
        cls,
        parent_instance: Union[DomainModel, SourceModel],
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in cls.context_index.index.doc_dbs:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        enabled_doc_db_name = parent_instance.enabled_doc_db.name

        provider_select_dd, service_providers_dict = GradioHelpers.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=enabled_doc_db_name,
            required_classes=cls.AVAILABLE_PROVIDERS,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict

    # def create_service_management_settings_ui(self):
    #     ui_components = {}

    #     with gr.Accordion(label="Pinecone"):
    #         pinecone_model_instance = self.context_index.get_or_create(
    #             name="pinecone_database"
    #         )
    #         pinecone_database = PineconeDatabase(config=pinecone_model_instance.config)
    #         ui_components[
    #             "pinecone_database"
    #         ] = pinecone_database.create_provider_management_settings_ui()

    #     return ui_components
