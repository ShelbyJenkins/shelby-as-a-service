from datetime import datetime, timedelta
from typing import Any, Optional

import context_index.doc_index as doc_index_models
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService
from services.service_base import ServiceBase
from services.text_processing.ingest_processing.ingest_processing_service import (
    IngestProcessingService,
)
from sqlalchemy.orm import Session, object_session


class DocIngest(ServiceBase):
    CLASS_NAME: str = "doc_ingest"
    CLASS_UI_NAME: str = "doc_ingest"

    update_frequency: int = 1  # In hours

    @classmethod
    def ingest_docs_from_context_index_source_or_domain(
        cls,
        source: Optional[doc_index_models.SourceModel] = None,
        domain: Optional[doc_index_models.DomainModel] = None,
    ):
        cls.log = cls.logger_wrapper(DocIngest.__name__)
        if source:
            sources = [source]
        elif domain:
            sources = domain.sources
        else:
            raise ValueError("Must provide either source or domain")

        cls.doc_index.commit_session
        cls.doc_index.close_session

        for source in sources:
            session = cls.doc_index.get_session()
            session.add(source)
            last_successful_update = getattr(source, "date_of_last_successful_update")
            if last_successful_update is None:
                last_successful_update = "Never"
            cls.log.info(
                f"Now ingesting source: {source.name}\n From uri: {source.source_uri}\n Last successfully updated: {last_successful_update}"
            )
            if isinstance(last_successful_update, datetime) and (
                datetime.utcnow() - last_successful_update
            ) > timedelta(minutes=cls.update_frequency):
                cls.log.info(
                    f"Skipping {source.name} because it was updated less than {cls.update_frequency} hours ago."
                )
                continue

            retry_count = 2
            for i in range(retry_count):
                if object_session(source) is None:
                    session = cls.doc_index.get_session()
                    session.add(source)
                try:
                    if cls.ingest_source(source=source, session=session):
                        session.commit()
                        break
                except Exception as error:
                    cls.log.info(f"An error occurred: {error}")
                    session.rollback()
                    cls.log.info(f"Retrying source. Attempt {i + 1} out of {retry_count}.")
                    if i == retry_count - 1:
                        cls.log.info(f"Skippng source after {i + 1} retries.")
                finally:
                    session.close()

        cls.log.info("end_log")
        cls.doc_index.open_session
        return

    @classmethod
    def ingest_source(cls, source: doc_index_models.SourceModel, session: Session) -> bool:
        if (
            ingest_docs := DocLoadingService().load_docs_from_context_index_source(source=source)
        ) is None:
            raise ValueError(f"Could not load docs from {source.name}")

        (
            upsert_docs,
            doc_db_ids_requiring_deletion,
        ) = IngestProcessingService().process_documents_from_context_index_source(
            ingest_docs=ingest_docs, source=source, session=session
        )

        if not upsert_docs:
            raise ValueError(f"Could not process docs from {source.name}")

        doc_db_service = DatabaseService()
        doc_db_service.upsert_documents_from_context_index_source(
            upsert_docs=upsert_docs, source=source
        )
        if doc_db_ids_requiring_deletion:
            doc_db_service.clear_existing_entries_by_id(
                domain_name=source.domain_model.name,
                doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
            )

        return True
