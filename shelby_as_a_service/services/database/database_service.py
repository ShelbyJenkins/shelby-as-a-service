from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
import services.database as database
from context_index.doc_index.context_docs import IngestDoc
from services.database.database_base import DatabaseBase
from services.embedding.embedding_service import EmbeddingService
from services.gradio_interface.gradio_base import GradioBase


class DatabaseService(DatabaseBase):
    CLASS_NAME: str = "database_service"

    CLASS_UI_NAME: str = "Document Databases"
    REQUIRED_CLASSES: list[Type] = database.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = database.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_TYPINGS = database.AVAILABLE_PROVIDERS_TYPINGS
    list_of_doc_db_provider_instances: list[DatabaseBase] = []
    current_doc_db_provider: DatabaseBase

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.list_of_doc_db_provider_instances = self.list_of_required_class_instances
        doc_db_provider_name = kwargs.get("doc_db_provider_name", None)
        if doc_db_provider_name:
            self.current_doc_db_provider = self.get_requested_class_instance(
                requested_class=doc_db_provider_name,
                available_classes=self.list_of_doc_db_provider_instances,
            )

    def get_doc_db_instance(
        self,
        doc_db_provider_name: Optional[database.AVAILABLE_PROVIDERS_TYPINGS] = None,
        doc_index_db_instance: Optional[DatabaseBase] = None,
    ) -> DatabaseBase:
        if doc_db_provider_name and doc_index_db_instance:
            raise ValueError(
                "Must provide either doc_db_provider_name or doc_index_db_instance, not both."
            )
        if doc_db_provider_name:
            doc_db = self.get_requested_class_instance(
                requested_class=doc_db_provider_name,
                available_classes=self.list_of_doc_db_provider_instances,
            )
        elif doc_index_db_instance:
            doc_db = doc_index_db_instance
        else:
            doc_db = self.current_doc_db_provider
        if doc_db is None:
            raise ValueError("doc_db must not be None")
        return doc_db

    def query_by_terms(
        self,
        domain_name: str,
        search_terms: list[str] | str,
        retrieve_n_docs: Optional[int] = None,
        doc_db_provider_name: Optional[database.AVAILABLE_PROVIDERS_TYPINGS] = None,
        doc_index_db_instance: Optional[DatabaseBase] = None,
    ) -> list[dict]:
        doc_db = self.get_doc_db_instance(
            doc_db_provider_name=doc_db_provider_name,
            doc_index_db_instance=doc_index_db_instance,
        )
        if isinstance(search_terms, str):
            search_terms = [search_terms]
        retrieved_docs = []
        for term in search_terms:
            docs = doc_db.query_by_terms_with_provider(
                search_terms=term, retrieve_n_docs=retrieve_n_docs, domain_name=domain_name
            )
            if docs:
                retrieved_docs.extend(docs)
            else:
                self.log.info(f"No documents found for {term}")
        return retrieved_docs

    def fetch_by_ids(
        self,
        domain_name: str,
        ids: list[int] | int,
        doc_db_provider_name: Optional[database.AVAILABLE_PROVIDERS_TYPINGS] = None,
        doc_index_db_instance: Optional[DatabaseBase] = None,
    ) -> list[dict]:
        doc_db = self.get_doc_db_instance(
            doc_db_provider_name=doc_db_provider_name,
            doc_index_db_instance=doc_index_db_instance,
        )
        if isinstance(ids, int):
            ids = [ids]

        docs = doc_db.fetch_by_ids_with_provider(ids=ids, domain_name=domain_name)
        if not docs:
            self.log.info(f"No documents found for {id}")
        return docs

    def upsert(
        self,
        entries_to_upsert: list[dict[str, Any]],
        domain_name: str,
        doc_db_provider_name: Optional[database.AVAILABLE_PROVIDERS_TYPINGS] = None,
        doc_index_db_instance: Optional[DatabaseBase] = None,
    ):
        doc_db = self.get_doc_db_instance(
            doc_db_provider_name=doc_db_provider_name,
            doc_index_db_instance=doc_index_db_instance,
        )
        current_entry_count = doc_db.get_index_domain_or_source_entry_count_with_provider(
            domain_name=domain_name
        )
        self.log.info(f"Upserting {len(entries_to_upsert)} entries to {doc_db.CLASS_NAME}")

        response = doc_db.upsert_with_provider(
            entries_to_upsert=entries_to_upsert, domain_name=domain_name
        )

        post_upsert_entry_count = doc_db.get_index_domain_or_source_entry_count_with_provider(
            domain_name=domain_name
        )
        if post_upsert_entry_count - current_entry_count != len(entries_to_upsert):
            raise ValueError(
                f"Upserted {len(entries_to_upsert)} entries but expected to upsert {post_upsert_entry_count - current_entry_count}.\n Response: {response}"
            )
        self.log.info(
            f"Successfully upserted {len(entries_to_upsert)} entries to {self.CLASS_NAME}.\n Response: {response}"
        )

    def clear_existing_entries_by_id(
        self,
        domain_name: str,
        doc_db_ids_requiring_deletion: list[str],
        doc_db_provider_name: Optional[database.AVAILABLE_PROVIDERS_TYPINGS] = None,
        doc_index_db_instance: Optional[DatabaseBase] = None,
    ):
        doc_db = self.get_doc_db_instance(
            doc_db_provider_name=doc_db_provider_name,
            doc_index_db_instance=doc_index_db_instance,
        )
        existing_entry_count = doc_db.get_index_domain_or_source_entry_count_with_provider(
            domain_name=domain_name
        )

        response = doc_db.clear_existing_entries_by_id_with_provider(
            doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
            domain_name=domain_name,
        )
        post_delete_entry_count = doc_db.get_index_domain_or_source_entry_count_with_provider(
            domain_name=domain_name
        )
        if existing_entry_count - post_delete_entry_count != len(doc_db_ids_requiring_deletion):
            raise ValueError(
                f"Deleted {len(doc_db_ids_requiring_deletion)} entries but expected to delete {existing_entry_count - post_delete_entry_count}.\n Response: {response}"
            )
        else:
            self.log.info(
                f"Deleted {len(doc_db_ids_requiring_deletion)} entries from {self.CLASS_NAME}.\n Response: {response}"
            )

    def upsert_documents_from_context_index_source(
        self, upsert_docs: list[IngestDoc], source: doc_index_models.SourceModel
    ):
        doc_index_db_instance: DatabaseBase = self.init_provider_instance_from_doc_index(
            domain_or_source=source
        )

        current_entry_count = (
            doc_index_db_instance.get_index_domain_or_source_entry_count_with_provider(
                domain_name=source.domain_model.name
            )
        )
        current_entry_count += 1
        chunks_to_upsert: list[doc_index_models.ChunkModel] = []
        chunk: doc_index_models.ChunkModel
        for doc in upsert_docs:
            if not doc.existing_document_model:
                raise ValueError(f"No existing_document_model for doc {doc.title}")
            if not doc.existing_document_model.context_chunks:
                raise ValueError(f"No context_chunks for doc {doc.title}")
            for i, chunk in enumerate(doc.existing_document_model.context_chunks):
                chunk_doc_db_id = f"id-{source.name}-{i + current_entry_count}"
                chunk.chunk_doc_db_id = chunk_doc_db_id
                chunks_to_upsert.append(chunk)

        entries_to_upsert = []
        if doc_index_db_instance.DOC_DB_REQUIRES_EMBEDDINGS:
            EmbeddingService(
                embedding_provider_name=source.enabled_doc_db.enabled_doc_embedder.name,
                embedding_model_name=source.enabled_doc_db.enabled_doc_embedder.config.get(
                    "current_embedding_model_name"
                ),
            ).get_document_embeddings_for_chunks_to_upsert(
                chunks_to_upsert=chunks_to_upsert, doc_index_db_model=source.enabled_doc_db
            )
            for chunk in chunks_to_upsert:
                metadata = chunk.prepare_upsert_metadata()
                entries_to_upsert.append(
                    doc_index_db_instance.prepare_upsert_for_vectorstore_with_provider(
                        id=chunk.chunk_doc_db_id, values=chunk.chunk_embedding, metadata=metadata
                    )
                )
        else:
            raise NotImplementedError

        self.upsert(
            entries_to_upsert=entries_to_upsert,
            domain_name=source.domain_model.name,
            doc_index_db_instance=doc_index_db_instance,
        )

    @classmethod
    def create_doc_index_ui_components(
        cls,
        parent_instance: doc_index_models.DomainModel | doc_index_models.SourceModel,
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in cls.doc_index.index.doc_dbs:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        enabled_doc_db_provider_name = parent_instance.enabled_doc_db.name

        provider_select_dd, service_providers_dict = GradioBase.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=enabled_doc_db_provider_name,
            required_classes=cls.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict

    # def create_service_management_settings_ui(self):
    #     ui_components = {}

    #     with gr.Accordion(label="Pinecone"):
    #         pinecone_model_instance = self.doc_index.get_or_create(
    #             name="pinecone_database"
    #         )
    #         pinecone_database = PineconeDatabase(config=pinecone_model_instance.config)
    #         ui_components[
    #             "pinecone_database"
    #         ] = pinecone_database.create_provider_management_settings_ui()

    #     return ui_components
