from datetime import datetime, timedelta
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
    update_frequency: int = 1  # In days

    @classmethod
    def ingest_docs_from_context_index_source_or_domain(
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

        cls.context_index.commit_context_index()

        for source in sources:
            last_successful_update = getattr(source, "date_of_last_successful_update", "Never")
            cls.log.info(
                f"Now ingesting: {source.name} @ {source.source_uri} last successfully updated: {last_successful_update}"
            )
            if isinstance(last_successful_update, datetime) and (
                datetime.utcnow() - last_successful_update
            ) > timedelta(hours=cls.update_frequency):
                cls.log.info(
                    f"Skipping {source.name} because it was updated less than {cls.update_frequency} hours ago."
                )
                continue

            retry_count = 3
            for i in range(retry_count):
                try:
                    if (
                        ingest_docs := DocLoadingService(
                            source=source
                        ).load_docs_from_context_index_source(
                            source=source,
                        )
                    ) is None:
                        cls.log.info(f"🔴 No documents found for {source.name}")
                        break

                    # Implement logic to update existing documents skipping one updated in most recent updates
                    upsert_docs, doc_db_ids_requiring_deletion = IngestProcessingService(
                        source=source
                    ).process_documents_from_context_index_source(ingest_docs=ingest_docs)
                    if not upsert_docs:
                        cls.log.info(f"🔴 No new or post-processed documents for {source.name}")
                        cls.context_index.session.rollback()
                        break

                    doc_db_service = DatabaseService(source=source)
                    doc_db_service.upsert_documents_from_context_index_source(
                        upsert_docs=upsert_docs,
                    )
                    doc_db_service.clear_existing_entries_by_id(
                        doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion
                    )
                    cls.context_index.commit_context_index()
                    break  # If completed successfully, break the retry loop
                except Exception as error:
                    cls.log.info(f"An error occurred: {error}")
                    cls.context_index.session.rollback()
                    if i < retry_count:
                        continue
                    else:
                        cls.log.info(f"An error occurred: {error} after {i} tries. Skipping.")
                        break
