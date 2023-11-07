from typing import Any, Dict, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers

# from modules.index.data_model import DataModels
from app.module_base import ModuleBase
from langchain.schema import Document
from services.context_index.context_index_model import DomainModel, SourceModel
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

    doc_loading_provider_name: DocLoadingService.AVAILABLE_PROVIDERS_NAMES = "generic_web_scraper"
    doc_ingest_processing_provider_name: IngestProcessingService.AVAILABLE_PROVIDERS_NAMES = (
        "ceq_ingest_processor"
    )
    doc_embedding_provider_name: str = "openai_embedding"
    doc_db_provider_name: str = "local_file_database"

    @classmethod
    def ingest_docs_from_source_or_domain(
        cls,
        source: Optional[SourceModel] = None,
        domain: Optional[DomainModel] = None,
    ):
        if source:
            sources = [source]
        elif domain:
            sources = domain.sources
        else:
            raise ValueError("Must provide either source or domain")

        cls.context_index.session.flush()

        for source in sources:
            cls.log.info(f"Now ingesting: {source.name} @ {source.source_uri}")
            retry_count = 3
            for i in range(retry_count):
                try:
                    if (
                        docs := DocLoadingService.load_docs_from_source(
                            source=source,
                        )
                    ) is None:
                        raise ValueError("No docs found")

                    docs = IngestProcessingService.preprocess_documents_from_source(
                        source=source,
                        docs=docs,
                    )

                    # Checks against local docs if there are changes or new docs
                    if IngestProcessingService.compare_new_and_existing_docs(
                        source=source,
                        docs=docs,
                    ):
                        cls.log.info(f"Skipping data_source: no new data found for {source.name}")
                        for doc in docs:
                            cls.context_index.session.expunge(doc)
                        return
                    # If there are changes or new docs, delete existing local files and write new files
                    DatabaseService.clear_existing_source_from_source(source)

                    IngestProcessingService.process_and_chunk_documents_from_source(
                        source=source,
                        docs=docs,
                    )
                    cls.context_index.session.flush()

                    DatabaseService.upsert_from_source(
                        source=source,
                        docs=docs,
                    )

                    break  # If completed successfully, break the retry loop
                except Exception as error:
                    cls.log.info(f"An error occurred: {error}")
                    if i < retry_count:
                        continue
                    else:
                        cls.log.info(f"An error occurred: {error} after {i} tries. Skipping.")
                        break

        # @classmethod
        # def ingest_docs(
        #     cls,
        #     uri: str,
        #     source: Optional[SourceModel],
        #     doc_loading_provider_name: Optional[DocLoadingService.AVAILABLE_PROVIDERS_NAMES] = None,
        #     doc_loading_provider_config: dict = {},
        #     doc_ingest_processing_provider_name: Optional[
        #         IngestProcessingService.AVAILABLE_PROVIDERS_NAMES
        #     ] = None,
        #     doc_ingest_processing_provider_config: dict = {},
        #     doc_embedding_provider_name: Optional[
        #         EmbeddingService.AVAILABLE_PROVIDERS_NAMES
        #     ] = None,
        #     doc_db_provider_name: Optional[DatabaseService.AVAILABLE_PROVIDERS_NAMES] = None,
        #     **kwargs,
        # ):
        #     cls.log.info(f"Now ingesting: {uri}\n")
        #     retry_count = 3
        #     for i in range(retry_count):
        #         try:
        #             doc_loading_provider_name = (
        #                 doc_loading_provider_name or cls.doc_loading_provider_name
        #             )
        #             if (
        #                 docs := DocLoadingService.load_docs_from_provider(
        #                     uri=uri,
        #                     provider_name=doc_loading_provider_name,
        #                     provider_config=doc_loading_provider_config,
        #                     **kwargs,
        #                 )
        #             ) is None:
        #                 return None

        #             doc_ingest_processing_provider_name = (
        #                 doc_ingest_processing_provider_name
        #                 or cls.doc_ingest_processing_provider_name
        #             )
        #             if (
        #                 docs := IngestProcessingService.process_documents_from_provider(
        #                     docs=docs,
        #                     provider_name=doc_ingest_processing_provider_name,
        #                     provider_config=doc_loading_provider_config,
        #                     **kwargs,
        #                 )
        #             ) is None:
        #                 return None
        #             if source:
        #                 pass
        #                 # here we add documents to database of existing documents

        #             # # Checks against local docs if there are changes or new docs
        #             # (
        #             #     has_changes,
        #             #     new_or_changed_chunks,
        #             # ) = data_source.preprocessor.compare_chunks(
        #             #     data_source, document_chunks
        #             # )
        #             # # If there are changes or new docs, delete existing local files and write new files
        #             # if not has_changes:
        #             #     cls.log.info(
        #             #         f"Skipping data_source: no new data found for {data_source.data_source_name}"
        #             #     )
        #             #     return
        #             # cls.log.info(f"Found {len(new_or_changed_chunks)} new or changed documents")

        #             break  # If completed successfully, break the retry loop
        #         except Exception as error:
        #             cls.log.info(f"An error occurred: {error}")
        #             if i < retry_count:
        #                 continue
        #             else:
        #                 cls.log.info(f"An error occurred: {error} after {i} tries. Skipping.")
        #                 break
