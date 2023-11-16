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
    def ingest_docs_from_doc_index_domains(
        cls, domains: doc_index_models.DomainModel | list[doc_index_models.DomainModel]
    ):
        cls.log = cls.logger_wrapper(DocIngest.__name__)
        if not isinstance(domains, list):
            domains = [domains]
        cls.doc_index.open_doc_index_write_session(domains)
        for domain in domains:
            cls.doc_index.open_doc_index_write_session(domain)
            cls.log.info(f"Starting ingest for domain: {domain.name}")
            cls.ingest_docs_from_doc_index_sources(domain.sources)

        cls.doc_index.close_doc_index_write_session

        return

    @classmethod
    def ingest_docs_from_doc_index_sources(
        cls, sources: doc_index_models.SourceModel | list[doc_index_models.SourceModel]
    ):
        cls.log = cls.logger_wrapper(DocIngest.__name__)

        if not isinstance(sources, list):
            sources = [sources]

        cls.doc_index.open_doc_index_write_session(sources)
        cls.ingest_sources(sources)

        cls.log.info("end_log")
        cls.doc_index.close_doc_index_write_session
        return

    @classmethod
    def ingest_sources(cls, sources: list[doc_index_models.SourceModel]):
        for source in sources:
            session = cls.doc_index.open_doc_index_write_session(sources)
            last_successful_update = getattr(source, "date_of_last_successful_update")
            if last_successful_update is None:
                last_successful_update = "Never"
            cls.log.info(
                f"\nNow ingesting source: {source.name}\n From uri: {source.source_uri}\n Last successfully updated: {last_successful_update}"
            )
            if isinstance(last_successful_update, datetime):
                if (datetime.utcnow() - last_successful_update) < timedelta(
                    minutes=cls.update_frequency
                ):
                    cls.log.info(
                        f"Skipping {source.name} because it was updated less than {cls.update_frequency} hours ago."
                    )
                    cls.doc_index.close_doc_index_write_session
                    continue

            retry_count = 2
            for i in range(retry_count):
                try:
                    if cls.ingest_source(source=source, session=session):
                        source.date_of_last_successful_update = datetime.utcnow()
                        session.commit()
                        cls.doc_index.close_doc_index_write_session
                        break
                except Exception as error:
                    cls.log.info(f"An error occurred: {error}")
                    session.rollback()
                    cls.log.info(f"Retrying source. Attempt {i + 1} out of {retry_count}.")
                    if i > retry_count - 1:
                        cls.log.info(f"Skippng source after {i + 1} retries.")
                finally:
                    cls.doc_index.close_doc_index_write_session

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
