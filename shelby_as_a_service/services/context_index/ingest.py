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

        cls.context_index.session.flush()

        for source in sources:
            cls.log.info(f"Now ingesting: {source.name} @ {source.source_uri}")
            retry_count = 3
            for i in range(retry_count):
                try:
                    if (
                        documents := DocLoadingService.load_docs_from_context_index_source(
                            source=source,
                        )
                    ) is None:
                        raise ValueError("No docs found")
                    # Implement logic to update existing documents skipping one updated in most recent updates
                    if (
                        document_models := IngestProcessingService.process_documents_from_context_index_source(
                            source=source,
                            documents=documents,
                        )
                    ) is None:
                        break

                    doc_db_instance = DatabaseService(source=source)
                    doc_db_instance.upsert_documents_from_context_index_source(
                        document_models=document_models,
                    )
                    cls.context_index.commit_context_index()
                    break  # If completed successfully, break the retry loop
                except Exception as error:
                    cls.log.info(f"An error occurred: {error}")
                    if i < retry_count:
                        continue
                    else:
                        cls.log.info(f"An error occurred: {error} after {i} tries. Skipping.")
                        cls.context_index.session.rollback()
                        break
