from datetime import datetime, timedelta
from typing import Any, Optional

import context_index.doc_index as doc_index_models
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService
from services.service_base import ServiceBase
from services.text_processing.ingest_processing.ingest_processing_service import (
    IngestProcessingService,
)


class DocIngest(ServiceBase):
    CLASS_NAME: str = "doc_ingest"
    CLASS_UI_NAME: str = "doc_ingest"

    update_frequency: int = 1  # In days

    @classmethod
    def ingest_docs_from_context_index_source_or_domain(
        cls,
        source: Optional[doc_index_models.SourceModel] = None,
        domain: Optional[doc_index_models.DomainModel] = None,
    ):
        if source:
            sources = [source]
        elif domain:
            sources = domain.sources
        else:
            raise ValueError("Must provide either source or domain")

        cls.doc_index.commit_context_index()

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
                    if cls.ingest_source(source=source):
                        break
                except Exception as error:
                    cls.log.info(f"An error occurred: {error}")
                    cls.doc_index.session.rollback()
                    if i < retry_count:
                        continue
                    else:
                        cls.log.info(f"An error occurred: {error} after {i} tries. Skipping.")
                        break

    @classmethod
    def ingest_source(cls, source: doc_index_models.SourceModel) -> bool:
        if (
            ingest_docs := DocLoadingService().load_docs_from_context_index_source(source=source)
        ) is None:
            cls.log.info(f"🔴 No documents found for {source.name}")
            return True

        (
            upsert_docs,
            doc_db_ids_requiring_deletion,
        ) = IngestProcessingService().process_documents_from_context_index_source(
            ingest_docs=ingest_docs, source=source
        )

        if not upsert_docs:
            cls.log.info(f"🔴 No new or post-processed documents for {source.name}")
            cls.doc_index.session.rollback()
            return True

        doc_db_service = DatabaseService()
        doc_db_service.upsert_documents_from_context_index_source(
            upsert_docs=upsert_docs, source=source
        )
        doc_db_service.clear_existing_entries_by_id(
            domain_name=source.domain_model.name,
            doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
        )
        cls.doc_index.commit_context_index()
        return True
