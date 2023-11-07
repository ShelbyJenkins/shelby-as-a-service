import os
import typing
from typing import Any, Dict, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
import pinecone
from app.module_base import ModuleBase
from pydantic import BaseModel


class PineconeDatabase(ModuleBase):
    CLASS_NAME: str = "pinecone_database"
    CLASS_UI_NAME: str = "Pinecone Database"
    REQUIRED_SECRETS: list[str] = ["pinecone_api_key"]

    class ClassConfigModel(BaseModel):
        index_env: str = "us-central1-gcp"
        index_name: str = "shelby-as-a-service"
        vectorstore_dimension: int = 1536
        upsert_batch_size: int = 20
        vectorstore_metric: str = "cosine"
        vectorstore_pod_type: str = "p1"

        retrieve_n_docs: int = 5
        indexed_metadata: list = [
            "data_domain_name",
            "data_source_name",
            "doc_type",
            "target_type",
            "date_indexed",
        ]

    config: ClassConfigModel
    existing_resource_vector_count: int

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        # super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.config = self.ClassConfigModel(**kwargs, **config_file_dict)

        if (api_key := self.secrets.get("pinecone_api_key")) is None:
            print("Pinecone API Key not found.")
        if api_key:
            pinecone.init(
                api_key=api_key,
                environment=self.config.index_env,
            )
            self.pinecone = pinecone
            self.pinecone_index = pinecone.Index(self.config.index_name)
            # indexes = pinecone.list_indexes()
        # if cls.index_name not in indexes:
        #     # create new index
        #     cls.create_index()
        #     indexes = pinecone.list_indexes()
        #     cls.log.info(f"Created index: {indexes}")

        #   cls.log.info(f"Initial index stats: {cls.vectorstore.describe_index_stats()}\n")
        #         index_resource_stats = self.pinecone_index.describe_index_stats(
        #     filter={"data_source_name": {"$eq": data_source.data_source_name}}
        # )

        # cls.log.info(
        # )
        # # cls.log.info(f'Post-upsert index stats: {index_resource_stats}\n')

    def clear_existing_source(self, domain_name: str, source_name: str):
        index_resource_stats = self.pinecone_index.describe_index_stats(
            filter={"target_type": {"$eq": source_name}}
        )
        existing_vector_count = (
            index_resource_stats.get("namespaces", {}).get(domain_name, {}).get("vector_count", 0)
        )
        self.log.info(f"Existing vector count for {source_name}: {existing_vector_count}")
        # If the "resource" already has vectors delete the existing vectors before upserting new vectors
        # We have to delete all because the difficulty in specifying specific documents in pinecone
        if existing_vector_count == 0:
            return
        self.pinecone_index.delete(
            namespace=domain_name,
            delete_all=False,
            filter={"data_source_name": {"$eq": source_name}},
        )
        index_resource_stats = self.pinecone_index.describe_index_stats(
            filter={"source_name": {"$eq": source_name}}
        )
        cleared_resource_vector_count = (
            index_resource_stats.get("namespaces", {}).get(domain_name, {}).get("vector_count", 0)
        )
        self.log.info(
            f"Removing pre-existing vectors. New count: {cleared_resource_vector_count} (should be 0)"
        )

    def upsert(self, docs, **kwargs):
        vectors_to_upsert = []
        vector_counter = self.existing_resource_vector_count + 1
        for i, story in enumerate(content):
            prepared_vector = {
                "id": f"id-{data_source.data_source_name}-{vector_counter}",
                "values": dense_embeddings[i],
                "metadata": document_chunk,
            }
            vector_counter += 1
            vectors_to_upsert.append(prepared_vector)

        self.log.info(f"Upserting {len(vectors_to_upsert)} vectors")
        self.pinecone_index.upsert(
            vectors=vectors_to_upsert,
            namespace=self.deployment_name,
            batch_size=self.config.upsert_batch_size,
            show_progress=True,
        )
        index_resource_stats = self.pinecone_index.describe_index_stats(
            filter={"data_source_name": {"$eq": data_source.data_source_name}}
        )
        new_resource_vector_count = (
            index_resource_stats.get("namespaces", {})
            .get(self.deployment_name, {})
            .get("vector_count", 0)
        )
        f"Previous vector count: {self.existing_resource_vector_count}\nNew vector count: {new_resource_vector_count}\n"

        self.log.info(f"Final index stats: {self.pinecone_index.describe_index_stats()}")

    def query_terms(
        self,
        search_terms,
        **kwargs,
    ) -> list[Any]:
        def _query_namespace(search_terms, top_k, namespace, filter=None):
            response = self.pinecone_index.query(
                top_k=self.config.retrieve_n_docs,
                include_values=False,
                namespace=namespace,
                include_metadata=True,
                filter=filter,  # type: ignore
                vector=search_terms,
            )

            returned_documents = []

            for m in response.matches:
                response = {
                    "content": m.metadata["content"],
                    "title": m.metadata["title"],
                    "url": m.metadata["url"],
                    "doc_type": m.metadata["doc_type"],
                    "score": m.score,
                    "id": m.id,
                }
                returned_documents.append(response)

            return returned_documents

        filter = None  # Need to implement

        if data_domain_name:
            namespace = data_domain_name
            returned_documents = _query_namespace(search_terms, top_k, namespace, filter)
        # If we don't have a namespace, just search all available namespaces
        else:
            pass
            # returned_documents = []
            # for data_domain in self.index.index_data_domains:
            #     if namespace := getattr(data_domain, "data_domain_name", None):
            #         returned_documents.extend(
            #             _query_namespace(search_terms, top_k, namespace, filter)
            #         )

        return returned_documents

        #     soft_filter = {
        #         "doc_type": {"$eq": "soft"},
        #         "data_domain_name": {"$in": data_domain_names},
        #     }

        #     hard_filter = {
        #         "doc_type": {"$eq": "hard"},
        #         "data_domain_name": {"$in": data_domain_names},
        #     }

        # else:
        #     soft_filter = {
        #         "doc_type": {"$eq": "soft"},
        #         "data_domain_name": {"$eq": data_domain_name},
        #     }
        #     hard_filter = {
        #         "doc_type": {"$eq": "hard"},
        #         "data_domain_name": {"$eq": data_domain_name},
        #     }
        # hard_query_response = self.pinecone_index.query(
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

    def fetch_by_ids(
        self,
        ids: list[int],
        **kwargs,
    ):
        namespace = kwargs.get("namespace", None)
        fetch_response = self.pinecone_index.fetch(
            namespace=namespace,
            ids=ids,
        )
        return fetch_response

    def delete_index(self):
        print(f"Deleting index {self.index_name}")
        stats = self.pinecone_index.describe_index_stats()
        print(stats)
        pinecone.delete_index(self.index_name)
        print(self.pinecone_index.describe_index_stats())

    def clear_index(self):
        print("Deleting all vectors in index.")
        stats = self.pinecone_index.describe_index_stats()
        print(stats)
        for key in stats["namespaces"]:
            self.pinecone_index.delete(deleteAll="true", namespace=key)
        print(self.pinecone_index.describe_index_stats())

    def clear_namespace(self):
        print(f"Clearing namespace aka deployment: {self.app_name}")
        self.pinecone_index.delete(deleteAll="true", namespace=self.app_name)
        print(self.pinecone_index.describe_index_stats())

    def create_index(self):
        metadata_config = {"indexed": self.config.index_indexed_metadata}
        # Prepare log message
        log_message = (
            f"Creating new index with the following configuration:\n"
            f" - Index Name: {self.index_name}\n"
            f" - Dimension: {self.config.index_vectorstore_dimension}\n"
            f" - Metric: {self.config.index_vectorstore_metric}\n"
            f" - Pod Type: {self.config.index_vectorstore_pod_type}\n"
            f" - Metadata Config: {metadata_config}"
        )
        # Log the message
        print(log_message)

        pinecone.create_index(
            name=self.index_name,
            dimension=self.config.index_vectorstore_dimension,
            metric=self.config.index_vectorstore_metric,
            pod_type=self.config.index_vectorstore_pod_type,
            metadata_config=metadata_config,
        )

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

    def create_provider_ui_components(self, visibility: bool = True) -> dict[str, Any]:
        ui_components = {}

        return ui_components
