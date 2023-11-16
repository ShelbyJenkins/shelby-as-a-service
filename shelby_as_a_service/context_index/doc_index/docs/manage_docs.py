import logging
from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
from context_index.doc_index.doc_index_base import DocIndexBase
from context_index.doc_index.doc_index_templates import DocIndexTemplates
from services.database.database_service import DatabaseService
from services.text_processing.text_utils import check_and_handle_name_collision
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class ManageDocs(DocIndexBase):
    CLASS_NAME: str = "doc_manage"
    CLASS_UI_NAME: str = "doc_manage"

    @classmethod
    def delete_document(cls, document: doc_index_models.DocumentModel) -> bool:
        cls.log = cls.logger_wrapper(ManageDocs.__name__)
        cls.open_write_session
        undeleted_chunks = []

        def delete_entries(doc_db_ids_requiring_deletion, chunk_doc_db_name):
            try:
                DatabaseService().clear_existing_entries_by_id(
                    domain_name=document.domain_model.name,
                    doc_db_provider_name=chunk_doc_db_name,  # type: ignore
                    doc_db_ids_requiring_deletion=doc_db_ids_requiring_deletion,
                )
            except Exception as error:
                cls.log.info(f"An error occurred: {error}")
                persisted_chunks = DatabaseService().fetch_by_ids(
                    domain_name=document.domain_model.name,
                    doc_db_provider_name=chunk_doc_db_name,  # type: ignore
                    ids=doc_db_ids_requiring_deletion,
                )
                if not persisted_chunks:
                    cls.log.info(
                        f"It seems like the chunks were deleted succesffuly despite the error."
                    )
                else:
                    cls.log.info(
                        f"Failed to delete the following chunks: '{persisted_chunks.keys()}'"
                    )
                    undeleted_chunks.extend(list(persisted_chunks.keys()))

        session = cls.open_doc_index_write_session(document)
        chunk_doc_db_name = None
        doc_db_ids_requiring_deletion = []

        for chunk in document.context_chunks:
            if chunk_doc_db_name is None:
                chunk_doc_db_name = chunk.chunk_doc_db_name
            if chunk_doc_db_name != chunk.chunk_doc_db_name:
                delete_entries(doc_db_ids_requiring_deletion, chunk_doc_db_name)
                chunk_doc_db_name = chunk.chunk_doc_db_name
                doc_db_ids_requiring_deletion = []
            doc_db_ids_requiring_deletion.append(chunk.chunk_doc_db_id)
        delete_entries(doc_db_ids_requiring_deletion, chunk_doc_db_name)

        if undeleted_chunks:
            ManageDocs.log.info(
                f"Failed to delete the following chunks for document: '{document.title}'. Persisting document."
            )
            cls.close_doc_index_write_session
            return False
        try:
            session.delete(document)
            session.flush()
            session.refresh(document.source_model.domain_model)
            cls.log.info(f"Successfully deleted document '{document.title}'")
        except Exception as error:
            cls.log.info(f"An error occurred: {error}")
            session.rollback()
            return False
        finally:
            cls.close_doc_index_write_session

        return True

    @classmethod
    def clear_source(cls, source: doc_index_models.SourceModel) -> bool:
        cls.log = cls.logger_wrapper(ManageDocs.__name__)
        session = cls.open_write_session()
        persisted_doc_index_docs = []
        deleted_doc_index_docs = []
        for document in source.documents:
            if not cls.delete_document(document=document):
                persisted_doc_index_docs.append(document)
            else:
                deleted_doc_index_docs.append(document)

        cls.close_write_session()
        if not persisted_doc_index_docs:
            cls.log.info(f"Successfully deleted all documents for {source.name}")
            return True
        else:
            undeleted_titles = [document.title for document in persisted_doc_index_docs]
            deleted_titles = [document.title for document in deleted_doc_index_docs]
            cls.log.info(
                f"Successfully deleted {deleted_titles}.\n"
                f"Failed to delete the following documents: {undeleted_titles}"
            )
            return False

    @classmethod
    def clear_domain(cls, domain: doc_index_models.DomainModel):
        cls.log = cls.logger_wrapper(ManageDocs.__name__)
        session = cls.open_write_session()
        domain_name = domain.name
        cleared_doc_index_sources: list[doc_index_models.SourceModel] = []
        uncleared_doc_index_sources: list[doc_index_models.SourceModel] = []
        for source in domain.sources:
            if cls.clear_source(source=source):
                cleared_doc_index_sources.append(source)
            else:
                uncleared_doc_index_sources.append(source)
        if not uncleared_doc_index_sources:
            cls.log.info(f"Successfully cleared all documents for {domain_name}")
        else:
            uncleared_sources = [source.name for source in uncleared_doc_index_sources]
            cleared_sources = [source.name for source in cleared_doc_index_sources]
            cls.log.info(
                f"Successfully cleared {cleared_sources}.\n"
                f"Failed to delete all documents for the following cleared: {uncleared_sources}"
            )
        cls.close_write_session()
