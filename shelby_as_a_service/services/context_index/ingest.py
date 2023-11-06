from __future__ import annotations

import typing
from typing import Any, Dict, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers

# from modules.index.data_model import DataModels
from app.module_base import ModuleBase
from langchain.schema import Document
from pydantic import BaseModel
from services.context_index.context_index_model import (
    ContextIndexModel,
    DocDBModel,
    DomainModel,
    SourceModel,
)
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService
from services.embedding.embedding_service import EmbeddingService
from services.text_processing.ingest_processing_service import IngestProcessingService


class DocIngest(ModuleBase):
    CLASS_NAME: str = "doc_ingest"
    CLASS_UI_NAME: str = "doc_ingest"
    REQUIRED_CLASSES: list[Type] = [
        DocLoadingService,
        IngestProcessingService,
        DatabaseService,
        EmbeddingService,
    ]

    doc_loading_provider_name: DocLoadingService.available_providers = "generic_web_scraper"
    doc_ingest_processing_provider_name: str = "ceq_ingest_processor"
    doc_embedding_provider_name: str = "sentence_transformers"
    doc_db_provider_name: str = "local_file_database"

    @classmethod
    def ingest_docs(
        cls,
        uri: str,
        doc_loading_provider_name: Optional[DocLoadingService.available_providers] = None,
        doc_loading_provider_config: dict = {},
        doc_ingest_processing_provider_name: Optional[str] = None,
        doc_ingest_processing_provider_config: dict = {},
        doc_db_provider_name: Optional[str] = None,
        doc_embedding_provider_name: Optional[str] = None,
        **kwargs,
    ):
        doc_loading_provider_name = doc_loading_provider_name or cls.doc_loading_provider_name
        docs = DocLoadingService.load_docs(
            uri=uri,
            provider_name=doc_loading_provider_name,
            provider_config=doc_loading_provider_config,
            **kwargs,
        )
        doc_ingest_processing_provider_name = (
            doc_ingest_processing_provider_name or cls.doc_ingest_processing_provider_name
        )
        docs = IngestProcessingService.process_documents(
            docs=docs,
            provider_name=doc_ingest_processing_provider_name,
            provider_config=doc_loading_provider_config,
            **kwargs,
        )
        # indexes = pinecone.list_indexes()
        # if self.index_name not in indexes:
        #     # create new index
        #     self.create_index()
        #     indexes = pinecone.list_indexes()
        #     self.log.info(f"Created index: {indexes}")
        # self.vectorstore = pinecone.Index(self.index_name)

        # ### Adds sources from yaml config file to queue ###

        # self.enabled_data_sources = []
        # # Iterate over each source aka namespace
        # for domain in self.index_description_file["data_domains"]:
        #     data_domain_name = domain["name"]
        #     domain_description = domain["description"]
        #     for data_source_name, source in domain["sources"].items():
        #         data_source = DataSourceConfig(
        #             self, data_domain_name, domain_description, data_source_name, source
        #         )
        #         if data_source.update_enabled == False:
        #             continue
        #         self.enabled_data_sources.append(data_source)
        #         self.log.info(f"Will index: {data_source_name}")

        self.log.info(f"Initial index stats: {self.vectorstore.describe_index_stats()}\n")

        for data_source in self.enabled_data_sources:
            # Retries if there is an error
            retry_count = 2
            for i in range(retry_count):
                try:
                    self.log.info(f"-----Now indexing: {data_source.data_source_name}\n")
                    # Get count of vectors in index matching the "resource" metadata field
                    index_resource_stats = data_source.vectorstore.describe_index_stats(
                        filter={"data_source_name": {"$eq": data_source.data_source_name}}
                    )
                    existing_resource_vector_count = (
                        index_resource_stats.get("namespaces", {})
                        .get(self.deployment_name, {})
                        .get("vector_count", 0)
                    )
                    self.log.info(
                        f"Existing vector count for {data_source.data_source_name}: {existing_resource_vector_count}"
                    )

                    # Load documents
                    documents = data_source.scraper.load()
                    if not documents:
                        self.log.info(
                            f"Skipping data_source: no data loaded for {data_source.data_source_name}"
                        )
                        break
                    self.log.info(f"Total documents loaded for indexing: {len(documents)}")

                    # Removes bad chars, and chunks text
                    document_chunks = data_source.preprocessor.run(documents)
                    if not document_chunks:
                        self.log.info(
                            f"Skipping data_source: no data after preprocessing {data_source.data_source_name}"
                        )
                        break
                    self.log.info(f"Total document chunks after processing: {len(document_chunks)}")

                    # Checks against local docs if there are changes or new docs
                    (
                        has_changes,
                        new_or_changed_chunks,
                    ) = data_source.preprocessor.compare_chunks(data_source, document_chunks)
                    # If there are changes or new docs, delete existing local files and write new files
                    if not has_changes:
                        self.log.info(
                            f"Skipping data_source: no new data found for {data_source.data_source_name}"
                        )
                        break
                    self.log.info(f"Found {len(new_or_changed_chunks)} new or changed documents")
                    (
                        text_chunks,
                        document_chunks,
                    ) = data_source.preprocessor.create_text_chunks(data_source, document_chunks)
                    self.log.info(
                        f"Total document chunks after final check: {len(document_chunks)}"
                    )

                    # Get dense_embeddings
                    dense_embeddings = data_source.embedding_retriever.embed_documents(text_chunks)

                    # If the "resource" already has vectors delete the existing vectors before upserting new vectors
                    # We have to delete all because the difficulty in specifying specific documents in pinecone
                    if existing_resource_vector_count != 0:
                        self._clear_data_source(data_source)
                        index_resource_stats = data_source.vectorstore.describe_index_stats(
                            filter={"data_source_name": {"$eq": data_source.data_source_name}}
                        )
                        cleared_resource_vector_count = (
                            index_resource_stats.get("namespaces", {})
                            .get(self.deployment_name, {})
                            .get("vector_count", 0)
                        )
                        self.log.info(
                            f"Removing pre-existing vectors. New count: {cleared_resource_vector_count} (should be 0)"
                        )

                    vectors_to_upsert = []
                    vector_counter = 0
                    for i, document_chunk in enumerate(document_chunks):
                        prepared_vector = {
                            "id": f"id-{data_source.data_source_name}-{vector_counter}",
                            "values": dense_embeddings[i],
                            "metadata": document_chunk,
                        }
                        vector_counter += 1
                        vectors_to_upsert.append(prepared_vector)

                    self.log.info(f"Upserting {len(vectors_to_upsert)} vectors")
                    # data_source.vectorstore.upsert(
                    #     vectors=vectors_to_upsert,
                    #     namespace=self.deployment_name,
                    #     batch_size=self.config.index_vectorstore_upsert_batch_size,
                    #     show_progress=True,
                    # )

                    index_resource_stats = data_source.vectorstore.describe_index_stats(
                        filter={"data_source_name": {"$eq": data_source.data_source_name}}
                    )
                    new_resource_vector_count = (
                        index_resource_stats.get("namespaces", {})
                        .get(self.deployment_name, {})
                        .get("vector_count", 0)
                    )
                    self.log.info(
                        f"Indexing complete for: {data_source.data_source_name}\nPrevious vector count: {existing_resource_vector_count}\nNew vector count: {new_resource_vector_count}\n"
                    )
                    # self.log.info(f'Post-upsert index stats: {index_resource_stats}\n')

                    data_source.preprocessor.write_chunks(data_source, document_chunks)

                    # If completed successfully, break the retry loop
                    break

                except Exception as error:
                    error_info = traceback.format_exc()
                    self.log.info(f"An error occurred: {error}\n{error_info}")
                    if i < retry_count - 1:  # i is zero indexed
                        continue  # this will start the next iteration of loop thus retrying your code block
                    else:
                        raise  # if exception in the last retry then raise it.

        self.log.info(f"Final index stats: {self.vectorstore.describe_index_stats()}")
