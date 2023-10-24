import os
from typing import Any, Dict, List, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
import pinecone
from app.module_base import ModuleBase
from pydantic import BaseModel


class PineconeDatabase(ModuleBase):
    CLASS_NAME: str = "pinecone_database"
    CLASS_UI_NAME: str = "Pinecone Database"
    REQUIRED_SECRETS: List[str] = ["pinecone_api_key"]

    class ClassConfigModel(BaseModel):
        index_env: str = "us-central1-gcp"
        index_name: str = "shelby-as-a-service"
        vectorstore_dimension: int = 1536
        vectorstore_upsert_batch_size: int = 20
        vectorstore_metric: str = "cosine"
        vectorstore_pod_type: str = "p1"

        preprocessor_min_length: int = 150
        #  text_splitter_goal_length: int = 500
        text_splitter_goal_length: int = 750
        text_splitter_overlap_percent: int = 15  # In percent
        retrieve_n_docs: int = 5
        indexed_metadata: List[str] = [
            "data_domain_name",
            "data_source_name",
            "doc_type",
            "target_type",
            "date_indexed",
        ]

    config: ClassConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)
        if (api_key := self.secrets.get("pinecone_api_key")) is None:
            print("Pinecone API Key not found.")
        if api_key:
            pinecone.init(
                api_key=api_key,
                environment=self.config.index_env,
            )
            self.pinecone = pinecone
            self.pinecone_index = pinecone.Index(self.config.index_name)

    def query_index(
        self,
        search_terms,
        retrieve_n_docs=None,
        data_domain_name=None,
    ) -> List[Any]:
        if retrieve_n_docs is None:
            top_k = self.config.retrieve_n_docs
        else:
            top_k = retrieve_n_docs

        def _query_namespace(search_terms, top_k, namespace, filter=None):
            response = self.pinecone_index.query(
                top_k=top_k,
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
            returned_documents = []
            for data_domain in self.index.index_data_domains:
                if namespace := getattr(data_domain, "data_domain_name", None):
                    returned_documents.extend(_query_namespace(search_terms, top_k, namespace, filter))

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

    def fetch_by_ids(self, ids, namespace=None) -> List[Any]:
        response = self.pinecone_index.fetch(
            namespace=namespace,
            ids=ids,
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

    def delete_pinecone_index(self):
        print(f"Deleting index {self.index_name}")
        stats = self.pinecone_index.describe_index_stats()
        print(stats)
        pinecone.delete_index(self.index_name)
        print(self.pinecone_index.describe_index_stats())

    def clear_pinecone_index(self):
        print("Deleting all vectors in index.")
        stats = self.pinecone_index.describe_index_stats()
        print(stats)
        for key in stats["namespaces"]:
            self.pinecone_index.delete(deleteAll="true", namespace=key)
        print(self.pinecone_index.describe_index_stats())

    def clear_pinecone_deployment(self):
        print(f"Clearing namespace aka deployment: {self.app_name}")
        self.pinecone_index.delete(deleteAll="true", namespace=self.app_name)
        print(self.pinecone_index.describe_index_stats())

    def clear_pinecone_data_source(self, data_source):
        data_source.pinecone_index.delete(
            namespace=self.app_name,
            delete_all=False,
            filter={"data_source_name": {"$eq": data_source.data_source_name}},
        )

    def create_pinecone_index(self):
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

    def create_settings_ui(self):
        components = {}
        with gr.Accordion(label=self.CLASS_UI_NAME, open=True):
            with gr.Column():
                components["index_env"] = gr.Textbox(
                    value=self.config.index_env, label="index_env", interactive=True, min_width=0
                )
                components["vectorstore_dimension"] = gr.Number(
                    value=self.config.vectorstore_dimension, label="vectorstore_dimension", interactive=True, min_width=0
                )
                components["vectorstore_upsert_batch_size"] = gr.Number(
                    value=self.config.vectorstore_upsert_batch_size,
                    label="vectorstore_upsert_batch_size",
                    interactive=True,
                    min_width=0,
                )
                components["vectorstore_metric"] = gr.Textbox(
                    value=self.config.vectorstore_metric, label="vectorstore_metric", interactive=True, min_width=0
                )
                components["vectorstore_pod_type"] = gr.Textbox(
                    value=self.config.vectorstore_pod_type, label="vectorstore_pod_type", interactive=True, min_width=0
                )
                components["indexed_metadata"] = gr.Dropdown(
                    value=self.config.indexed_metadata[0],
                    choices=self.config.indexed_metadata,
                    label="indexed_metadata",
                    interactive=True,
                    min_width=0,
                )
                GradioHelper.create_settings_event_listener(self.config, components)

        return components
