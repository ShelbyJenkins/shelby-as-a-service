import os
import typing
from typing import Any, Literal, Optional

import gradio as gr
import pinecone
from context_index.doc_index.docs.context_docs import RetrievalDoc
from pinecone import FetchResponse, QueryResponse
from pydantic import BaseModel, ValidationError
from services.database.database_base import DatabaseBase


class ClassConfigModel(BaseModel):
    index_env: str = "us-central1-gcp"
    index_name: str = "shelby-as-a-service"
    vectorstore_dimension: int = 1536
    upsert_batch_size: int = 20
    vectorstore_metric: str = "cosine"
    vectorstore_pod_type: str = "p1"
    enabled_doc_embedder_name: str = "openai_embedding"
    enabled_doc_embedder_config: dict[str, Any] = {}
    retrieve_n_docs: int = 5
    indexed_metadata: list = [
        "domain_name",
        "source_name",
        "source_type",
        "date_of_creation",
    ]

    class Config:
        extra = "ignore"


class PineconeDatabase(DatabaseBase):
    class_name = Literal["pinecone_database"]
    CLASS_NAME: str = typing.get_args(class_name)[0]
    CLASS_UI_NAME: str = "Pinecone Database"
    REQUIRED_SECRETS: list[str] = ["pinecone_api_key"]
    DOC_DB_REQUIRES_EMBEDDINGS: bool = True

    class_config_model = ClassConfigModel
    config: ClassConfigModel
    existing_entry_count: int
    domain_name: str
    source_name: Optional[str] = None
    pinecone_index: Optional[pinecone.Index] = None

    def __init__(
        self,
        index_env: Optional[str] = None,
        index_name: Optional[str] = None,
        vectorstore_dimension: Optional[int] = None,
        upsert_batch_size: Optional[int] = None,
        vectorstore_metric: Optional[str] = None,
        vectorstore_pod_type: Optional[str] = None,
        retrieve_n_docs: Optional[int] = None,
        context_index_config: dict[str, Any] = {},
        config_file_dict: dict[str, Any] = {},
        **kwargs,
    ):
        super().__init__(
            index_env=index_env,
            index_name=index_name,
            vectorstore_dimension=vectorstore_dimension,
            upsert_batch_size=upsert_batch_size,
            vectorstore_metric=vectorstore_metric,
            vectorstore_pod_type=vectorstore_pod_type,
            retrieve_n_docs=retrieve_n_docs,
            context_index_config=context_index_config,
            config_file_dict=config_file_dict,
            **kwargs,
        )

    def init_provider(self) -> pinecone.Index:
        if self.pinecone_index is not None:
            return self.pinecone_index
        if (api_key := self.secrets.get("pinecone_api_key")) is None:
            raise ValueError("Pinecone API Key not found.")
        pinecone.init(
            api_key=api_key,
            environment=self.config.index_env,
        )
        self.pinecone = pinecone
        indexes = pinecone.list_indexes()
        if self.config.index_name not in indexes:
            # create new index
            self.create_index()
            indexes = pinecone.list_indexes()
            self.log.info(f"Created index: {indexes}")
        self.pinecone_index = pinecone.Index(self.config.index_name)
        return self.pinecone_index

    def get_index_domain_or_source_entry_count_with_provider(
        self, source_name: Optional[str] = None, domain_name: Optional[str] = None
    ) -> int:
        pinecone_index = self.init_provider()
        # self.log.info(f"Complete index stats: {pinecone_index.describe_index_stats()}\n")
        if source_name:
            index_resource_stats = pinecone_index.describe_index_stats(
                filter={"source_name": {"$eq": source_name}}
            )
            total = index_resource_stats.get("total_vector_count", None)
            if not total:
                raise ValueError(f"'total_vector_count' not found.")
            return total
        elif domain_name:
            index_resource_stats = pinecone_index.describe_index_stats(
                filter={"domain_name": {"$eq": domain_name}}
            )
            namespaces = index_resource_stats.get("namespaces", {})
            if not isinstance(namespaces, dict):
                raise ValueError(f"'namespaces' not found.")
            domain = namespaces.get(domain_name, {})
            if not isinstance(domain, dict):
                raise ValueError(f"Domain {domain_name} not found.")
            vector_count = domain.get("vector_count", None)
            if not vector_count:
                self.log.info(f"Domain {domain_name} not found. Using total_vector_count.")
                total = index_resource_stats.get("total_vector_count", None)
                if not total:
                    raise ValueError(f"'total_vector_count' not found.")
                return total
            return vector_count

        else:
            raise ValueError("Must provide either source_name or domain_name")

    def clear_existing_source(self, source_name: str, domain_name: str) -> Any:
        return pinecone_index.delete(
            namespace=domain_name,
            delete_all=False,
            filter={"source_name": {"$eq": source_name}},
        )

    def clear_existing_entries_by_id_with_provider(
        self, doc_db_ids_requiring_deletion: list[str], domain_name: str
    ) -> bool:
        pinecone_index = self.init_provider()
        response = pinecone_index.delete(
            namespace=domain_name,
            delete_all=False,
            ids=doc_db_ids_requiring_deletion,
        )
        if response != {}:
            raise ValueError(f"Failed to delete ids due to error: {response}")
        return True

    def prepare_upsert_for_vectorstore_with_provider(
        self,
        id: str,
        values: Optional[list[float]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        if not values:
            raise ValueError(f"Must provide values for {self.CLASS_NAME}")
        return {
            "id": id,
            "values": values,
            "metadata": metadata,
        }

    def upsert_with_provider(
        self,
        entries_to_upsert: list[dict[str, Any]],
        domain_name: str,
    ) -> Any:
        pinecone_index = self.init_provider()
        return pinecone_index.upsert(
            vectors=entries_to_upsert,
            namespace=domain_name,
            batch_size=self.config.upsert_batch_size,
            show_progress=True,
        )

    def query_by_terms_with_provider(
        self,
        search_terms: list[float],
        domain_name: str,
        retrieve_n_docs: Optional[int] = None,
    ) -> list[RetrievalDoc]:
        pinecone_index = self.init_provider()
        filter = None  # Need to implement
        if retrieve_n_docs is None:
            top_k = self.config.retrieve_n_docs
        else:
            top_k = retrieve_n_docs

        response: QueryResponse = pinecone_index.query(
            top_k=top_k,
            include_values=False,
            namespace=domain_name,
            include_metadata=True,
            filter=filter,  # type: ignore
            vector=search_terms,
        )

        returned_documents = []
        matches: list[dict] = response.get("matches", {})
        for m in matches:
            metadata: dict[str, Any] = m.get("metadata", {})
            try:
                if not (context_chunk := metadata.get("context_chunk")):
                    context_chunk = metadata.get("content")
                if not context_chunk:
                    raise ValueError(
                        f"Neither 'context_chunk' nor 'content' found in metadata: {metadata}"
                    )
                returned_documents.append(
                    RetrievalDoc(
                        domain_name=metadata.get("domain_name"),
                        source_name=metadata.get("source_name"),
                        context_chunk=context_chunk,
                        document_id=metadata.get("document_id"),
                        title=metadata.get("title"),
                        uri=metadata.get("uri"),
                        source_type=metadata.get("source_type"),
                        score=m.get("score", 0),
                        chunk_doc_db_id=m.get("id"),
                        date_of_creation=metadata.get("date_of_creation"),
                    )
                )
            except ValidationError as e:
                self.log.error(f"Failed to validate metadata: {metadata} due to error: {e}")

        return returned_documents
        #     soft_filter = {
        #         "doc_type": {"$eq": "soft"},
        #         "domain_name": {"$in": domain_names},
        #     }

        #     hard_filter = {
        #         "doc_type": {"$eq": "hard"},
        #         "domain_name": {"$in": domain_names},
        #     }

        # else:
        #     soft_filter = {
        #         "doc_type": {"$eq": "soft"},
        #         "domain_name": {"$eq": domain_name},
        #     }
        #     hard_filter = {
        #         "doc_type": {"$eq": "hard"},
        #         "domain_name": {"$eq": domain_name},
        #     }
        # hard_query_response = pinecone_index.query(
        #     top_k=retrieve_n_docs,
        #     include_values=False,
        #     namespace=AppBase.app_config.app_name,
        #     include_metadata=True,
        #     filter=hard_filter,
        #     vector=dense_embedding

        # )

        # Destructures the QueryResponse object the pinecone library generates.
        # for m in hard_query_response.matches:
        #     response = {
        #         "content": m.metadata["content"],
        #         "title": m.metadata["title"],
        #         "url": m.metadata["url"],
        #         "doc_type": m.metadata["doc_type"],
        #         "score": m.score,
        #         "id": m.id,
        #     }
        #     returned_documents.append(response)

    def fetch_by_ids_with_provider(
        self,
        ids: list[str],
        domain_name: str,
    ) -> dict[str, Any] | None:
        pinecone_index = self.init_provider()
        fetch_response: FetchResponse = pinecone_index.fetch(
            namespace=domain_name,
            ids=ids,
        )
        if (vectors := fetch_response.get("vectors", None)) is None:
            self.log.info(f"Vectors not found in fetch response: {fetch_response}")
            return None
        return vectors

    # def delete_index(self):
    #     print(f"Deleting index {self.index_name}")
    #     stats = pinecone_index.describe_index_stats()
    #     print(stats)
    #     pinecone.delete_index(self.index_name)
    #     print(pinecone_index.describe_index_stats())

    # def clear_index(self):
    #     print("Deleting all vectors in index.")
    #     stats = pinecone_index.describe_index_stats()
    #     print(stats)
    #     for key in stats["namespaces"]:
    #         pinecone_index.delete(deleteAll="true", namespace=key)
    #     print(pinecone_index.describe_index_stats())

    # def clear_namespace(self):
    #     print(f"Clearing namespace aka deployment: {self.app_name}")
    #     pinecone_index.delete(deleteAll="true", namespace=self.app_name)
    #     print(pinecone_index.describe_index_stats())

    # def create_index(self):
    #     metadata_config = {"indexed": self.config.index_indexed_metadata}
    #     # Prepare log message
    #     log_message = (
    #         f"Creating new index with the following configuration:\n"
    #         f" - Index Name: {self.index_name}\n"
    #         f" - Dimension: {self.config.index_vectorstore_dimension}\n"
    #         f" - Metric: {self.config.index_vectorstore_metric}\n"
    #         f" - Pod Type: {self.config.index_vectorstore_pod_type}\n"
    #         f" - Metadata Config: {metadata_config}"
    #     )
    #     # Log the message
    #     print(log_message)

    #     pinecone.create_index(
    #         name=self.index_name,
    #         dimension=self.config.index_vectorstore_dimension,
    #         metric=self.config.index_vectorstore_metric,
    #         pod_type=self.config.index_vectorstore_pod_type,
    #         metadata_config=metadata_config,
    #     )

    def create_provider_management_settings_ui(self):
        ui_components = {}

        ui_components["index_env"] = gr.Textbox(
            value=self.config.index_env, label="index_env", interactive=True, min_width=0
        )
        ui_components["vectorstore_dimension"] = gr.Number(
            value=self.config.vectorstore_dimension,
            label="vectorstore_dimension",
            interactive=True,
            min_width=0,
        )
        ui_components["vectorstore_metric"] = gr.Textbox(
            value=self.config.vectorstore_metric,
            label="vectorstore_metric",
            interactive=True,
            min_width=0,
        )
        ui_components["vectorstore_pod_type"] = gr.Textbox(
            value=self.config.vectorstore_pod_type,
            label="vectorstore_pod_type",
            interactive=True,
            min_width=0,
        )
        ui_components["indexed_metadata"] = gr.Dropdown(
            value=self.config.indexed_metadata[0],
            choices=self.config.indexed_metadata,
            label="indexed_metadata",
            interactive=True,
            min_width=0,
            multiselect=True,
            allow_custom_value=True,
        )
        ui_components["upsert_batch_size"] = gr.Number(
            value=self.config.upsert_batch_size,
            label="upsert_batch_size",
            interactive=True,
            min_width=0,
        )

        return ui_components

    @classmethod
    def create_provider_ui_components(cls, config_model: ClassConfigModel, visibility: bool = True):
        ui_components = {}

        return ui_components
