import logging
from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
from context_index.doc_index.doc_index_base import DocIndexBase
from services.database.database_service import DatabaseService
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class ManageDocs(DocIndexBase):
    CLASS_NAME: str = "doc_manage"
    CLASS_UI_NAME: str = "doc_manage"

    @classmethod
    def clear_domains(
        cls, domains: list[doc_index_models.DomainModel] | doc_index_models.DomainModel
    ):
        cls.log = cls.logger_wrapper(ManageDocs.__name__)
        session = cls.open_write_session()
        persisted_chunk_models: list[doc_index_models.ChunkModel] = []
        deletion_chunk_models: list[doc_index_models.ChunkModel] = []

        if not isinstance(domains, list):
            domains = [domains]
        for domain in domains:
            for source in domain.sources:
                deletion_chunk_models.extend(cls._get_chunk_models_from_sources(sources=source))
        if not deletion_chunk_models:
            cls.log.info(
                f"Failed to find any chunks for the following domains: {[domain.name for domain in domains]}"
            )
        else:
            persisted_chunk_models = cls._delete_chunks_from_doc_db(
                chunk_models=deletion_chunk_models, session=session
            )

            persisted_docs = cls._delete_documents(
                deletion_chunk_models=deletion_chunk_models,
                persisted_chunk_models=persisted_chunk_models,
                session=session,
            )

            uncleared_sources: set[doc_index_models.SourceModel] = {
                document.source_model for document in persisted_docs
            }
            uncleared_domains: set[doc_index_models.DomainModel] = {
                document.domain_model for document in persisted_docs
            }

            if not uncleared_domains and not uncleared_sources:
                cls.log.info(
                    f"Successfully cleared all documents for domains: {[domain.name for domain in domains]}"
                )
                cls.log.info(
                    f"Successfully cleared all documents for sources: {[source.name for domain in domains for source in domain.sources]}"
                )
            if uncleared_domains:
                cls.log.info(
                    f"Failed to delete all documents for domains: {[domain.name for domain in uncleared_domains]}"
                )
            if uncleared_sources:
                cls.log.info(
                    f"Failed to delete all documents for sources: {[source.name for source in uncleared_sources]}"
                )

        cls.close_write_session()
        cls.log.info("end_log")

    @classmethod
    def clear_sources(
        cls, sources: list[doc_index_models.SourceModel] | doc_index_models.SourceModel
    ):
        cls.log = cls.logger_wrapper(ManageDocs.__name__)
        session = cls.open_write_session()
        persisted_chunk_models: list[doc_index_models.ChunkModel] = []
        deletion_chunk_models: list[doc_index_models.ChunkModel] = []
        if not isinstance(sources, list):
            sources = [sources]
        for source in sources:
            deletion_chunk_models.extend(cls._get_chunk_models_from_sources(sources=source))

        if not deletion_chunk_models:
            cls.log.info(
                f"Failed to find any chunks for the following sources: {[source.name for source in sources]}"
            )
        else:
            persisted_chunk_models = cls._delete_chunks_from_doc_db(
                chunk_models=deletion_chunk_models, session=session
            )

            persisted_docs = cls._delete_documents(
                deletion_chunk_models=deletion_chunk_models,
                persisted_chunk_models=persisted_chunk_models,
                session=session,
            )
            uncleared_sources: set[doc_index_models.SourceModel] = {
                document.source_model for document in persisted_docs
            }
            if not uncleared_sources:
                cls.log.info(
                    f"Successfully cleared all documents for sources: {[source.name for source in sources]}"
                )
            if uncleared_sources:
                cls.log.info(
                    f"Failed to delete all documents for sources: {[source.name for source in uncleared_sources]}"
                )
        cls.close_write_session()
        cls.log.info("end_log")

    @classmethod
    def delete_documents(
        cls,
        documents: list[doc_index_models.DocumentModel] | doc_index_models.DocumentModel,
        session: Session,
    ):
        cls.log = cls.logger_wrapper(ManageDocs.__name__)
        cls.open_write_session
        deletion_chunk_models: list[doc_index_models.ChunkModel] = []
        if not isinstance(documents, list):
            documents = [documents]
        for document in documents:
            deletion_chunk_models.extend(document.context_chunks)

        persisted_chunk_models = cls._delete_chunks_from_doc_db(
            chunk_models=deletion_chunk_models, session=session
        )
        persisted_docs = cls._delete_documents(
            deletion_chunk_models=deletion_chunk_models,
            persisted_chunk_models=persisted_chunk_models,
            session=session,
        )
        if persisted_docs:
            cls.log.info(
                f"Failed to delete documents: {[document.title for document in persisted_docs]}"
            )
        else:
            cls.log.info(
                f"Successfully deleted all documents: {[document.title for document in documents]}"
            )
        cls.close_write_session()
        cls.log.info("end_log")

    @classmethod
    def _get_chunk_models_from_sources(
        cls, sources: list[doc_index_models.SourceModel] | doc_index_models.SourceModel
    ) -> list[doc_index_models.ChunkModel]:
        chunk_models: list[doc_index_models.ChunkModel] = []
        if not isinstance(sources, list):
            sources = [sources]
        for source in sources:
            for document in source.documents:
                chunk_models.extend(document.context_chunks)
        if not chunk_models:
            cls.log.info(
                f"Failed to find any chunks for the following sources: {[source.name for source in sources]}"
            )

        return chunk_models

    @classmethod
    def _delete_chunks_from_doc_db(
        cls, chunk_models: list[doc_index_models.ChunkModel], session: Session
    ) -> list[doc_index_models.ChunkModel]:
        chunk_doc_db_name = None
        domain_name = None
        doc_db_ids_requiring_deletion = []
        persisted_doc_db_ids = []

        for chunk in chunk_models:
            if chunk_doc_db_name is None or domain_name is None:
                chunk_doc_db_name = chunk.chunk_doc_db_name
                domain_name = chunk.document_model.domain_model.name

            if (
                chunk_doc_db_name != chunk.chunk_doc_db_name
                or domain_name != chunk.document_model.domain_model.name
            ):
                persisted_doc_db_ids.extend(
                    cls._delete_doc_db_entries(
                        doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
                        domain_name=domain_name,
                        chunk_doc_db_name=chunk_doc_db_name,
                    )
                )
                chunk_doc_db_name = chunk.chunk_doc_db_name
                domain_name = chunk.document_model.domain_model.name
                doc_db_ids_requiring_deletion = []

            doc_db_ids_requiring_deletion.append(chunk.chunk_doc_db_id)

        if domain_name and chunk_doc_db_name and doc_db_ids_requiring_deletion:
            persisted_doc_db_ids.extend(
                cls._delete_doc_db_entries(
                    doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
                    domain_name=domain_name,
                    chunk_doc_db_name=chunk_doc_db_name,
                )
            )
        else:
            cls.log.info("No chunks to delete found in _delete_chunks_from_doc_db.")

        if persisted_doc_db_ids:
            return cls._get_chunk_models_for_persisted_doc_db_ids(
                persisted_doc_db_ids=persisted_doc_db_ids, session=session
            )
        return []

    @classmethod
    def _delete_doc_db_entries(
        cls, doc_db_ids_requiring_deletion: list[str], domain_name: str, chunk_doc_db_name: str
    ) -> list[str]:
        try:
            DatabaseService().clear_existing_entries_by_id(
                domain_name=domain_name,
                doc_db_provider_name=chunk_doc_db_name,  # type: ignore
                doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
            )
        except Exception as error:
            cls.log.info(f"An error occurred: {error}")
            persisted_doc_db_chunks = DatabaseService().fetch_by_ids(
                domain_name=domain_name,
                doc_db_provider_name=chunk_doc_db_name,  # type: ignore
                ids=doc_db_ids_requiring_deletion,
            )
            if persisted_doc_db_chunks:
                cls.log.info(
                    f"Failed to delete the following chunks: '{persisted_doc_db_chunks.keys()}'"
                )
                return list(persisted_doc_db_chunks.keys())
            else:
                cls.log.info(
                    f"It seems like the chunks were deleted succesffuly despite the error."
                )
        finally:
            return []

    @classmethod
    def _get_chunk_models_for_persisted_doc_db_ids(
        cls, persisted_doc_db_ids: list[str], session: Session
    ) -> list[doc_index_models.ChunkModel]:
        persisted_chunk_models: list[doc_index_models.ChunkModel] = []

        for doc_db_id in persisted_doc_db_ids:
            chunk_model = (
                session.query(doc_index_models.ChunkModel)
                .filter(doc_index_models.ChunkModel.chunk_doc_db_id == doc_db_id)
                .first()
            )
            if not chunk_model:
                cls.log.info(f"Failed to find chunk with id: {doc_db_id}")
                continue
            persisted_chunk_models.append(chunk_model)

        return persisted_chunk_models

    @classmethod
    def _delete_documents(
        cls,
        deletion_chunk_models: list[doc_index_models.ChunkModel],
        persisted_chunk_models: list[doc_index_models.ChunkModel],
        session: Session,
    ) -> set[doc_index_models.DocumentModel]:
        deletions_docs: set[doc_index_models.DocumentModel] = set()
        persisted_docs: set[doc_index_models.DocumentModel] = set()
        for chunk in persisted_chunk_models:
            persisted_docs.add(chunk.document_model)
        for chunk in deletion_chunk_models:
            if chunk.document_model not in persisted_docs:
                deletions_docs.add(chunk.document_model)
        for doc in deletions_docs:
            try:
                session.delete(doc)
                session.flush()
                cls.log.info(f"Successfully deleted document '{doc.title}'")
            except Exception as error:
                cls.log.info(f"An error occurred: {error}")
                session.rollback()

        if persisted_docs:
            ManageDocs.log.info(
                f"Failed to delete the following chunks for document: '{[document.title for document in persisted_docs]}'. Persisting document."
            )
            return persisted_docs
        return set()
