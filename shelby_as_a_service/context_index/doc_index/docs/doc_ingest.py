from datetime import datetime, timedelta

import context_index.doc_index as doc_index_models
from context_index.doc_index.doc_index_base import DocIndexBase
from services.database.database_service import DatabaseService
from services.document_loading.document_loading_service import DocLoadingService
from services.text_processing.ingest_processing.ingest_processing_service import (
    IngestProcessingService,
)
from sqlalchemy.orm import Session


class DocIngest(DocIndexBase):
    CLASS_NAME: str = "doc_ingest"
    CLASS_UI_NAME: str = "doc_ingest"

    update_frequency: int = 1  # In hours

    @classmethod
    def ingest_docs_from_doc_index_domains(
        cls, domains: doc_index_models.DomainModel | list[doc_index_models.DomainModel]
    ):
        cls.log = cls.logger_wrapper(DocIngest.__name__)
        session = cls.open_write_session()

        if not isinstance(domains, list):
            domains = [domains]
        if not domains:
            cls.log.info("No domains found. The index should have at least one domain.")
            return

        for domain in domains:
            cls.log.info(f"Starting ingest for domain: {domain.name}")
            sources: list[doc_index_models.SourceModel] = domain.sources

            if not sources:
                cls.log.info(
                    f"No sources found for domain: {domain.name}. All domains should have at least one source."
                )
                continue

            cls._ingest_sources(sources=sources, session=session)

        cls.log.info("end_log")
        cls.close_write_session()
        return

    @classmethod
    def ingest_docs_from_doc_index_sources(
        cls, sources: doc_index_models.SourceModel | list[doc_index_models.SourceModel]
    ):
        cls.log = cls.logger_wrapper(DocIngest.__name__)
        session = cls.open_write_session()

        if not isinstance(sources, list):
            sources = [sources]

        cls._ingest_sources(sources=sources, session=session)

        cls.log.info("end_log")
        cls.close_write_session()
        return

    @classmethod
    def _ingest_sources(cls, sources: list[doc_index_models.SourceModel], session: Session):
        for source in sources:
            last_successful_update = getattr(source, "date_of_last_successful_update")
            if last_successful_update is None:
                last_successful_update = "Never"
            if isinstance(last_successful_update, datetime):
                if (datetime.utcnow() - last_successful_update) < timedelta(
                    minutes=cls.update_frequency
                ):
                    cls.log.info(
                        f"Skipping {source.name} because it was updated less than {cls.update_frequency} hours ago."
                    )
                    continue

            cls.log.info(
                f"\nNow ingesting source: {source.name}\n From uri: {source.source_uri}\n Last successfully updated: {last_successful_update}"
            )
            retry_count = 2
            for i in range(retry_count):
                try:
                    if cls._ingest_source(source=source, session=session):
                        source.date_of_last_successful_update = datetime.utcnow()
                        session.commit()
                        break
                except Exception as error:
                    cls.log.info(f"An error occurred: {error}")
                    session.rollback()
                    cls.log.info(f"Retrying source. Attempt {i + 1} out of {retry_count}.")
                    if i > retry_count - 1:
                        cls.log.info(f"Skippng source after {i + 1} retries.")

    @classmethod
    def _ingest_source(cls, source: doc_index_models.SourceModel, session: Session) -> bool:
        doc_loader_model: doc_index_models.DocLoaderModel = source.enabled_doc_loader
        if (
            ingest_docs := DocLoadingService(
                doc_loader_provider_name=doc_loader_model.name,  # type: ignore
                context_index_config=doc_loader_model.config,
            ).load_docs_from_context_index_source(source=source)
        ) is None:
            raise ValueError(f"Could not load docs from {source.name}")

        doc_ingest_processor_model: doc_index_models.DocIngestProcessorModel = (
            source.enabled_doc_ingest_processor
        )
        (
            upsert_docs,
            doc_db_ids_requiring_deletion,
        ) = IngestProcessingService(
            doc_ingest_processor_name=doc_ingest_processor_model.name,  # type: ignore
            context_index_config=doc_ingest_processor_model.config,
            session=session,
        ).process_documents_from_context_index_source(ingest_docs=ingest_docs, source=source)

        if not upsert_docs:
            raise ValueError(f"Could not process docs from {source.name}")

        doc_db_model: doc_index_models.DocDBModel = source.enabled_doc_db
        doc_embedding_model: doc_index_models.DocEmbeddingModel = doc_db_model.enabled_doc_embedder
        doc_db_service = DatabaseService(
            doc_db_provider_name=doc_db_model.name,  # type: ignore
            doc_db_embedding_provider_name=doc_embedding_model.name,  # type: ignore
            doc_db_embedding_provider_config=doc_embedding_model.config,
            context_index_config=doc_db_model.config,
            session=session,
        )
        doc_db_service.upsert_documents_from_context_index_source(
            upsert_docs=upsert_docs,
            source=source,
            doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
        )
        if doc_db_ids_requiring_deletion:
            doc_db_service.clear_existing_entries_by_id(
                domain_name=source.domain_model.name,
                doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
            )

        return True
