from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
import services.text_processing.ingest_processing as ingest_processing
import services.text_processing.text_utils as text_utils
from context_index.doc_index.docs.context_docs import IngestDoc
from services.gradio_interface.gradio_base import GradioBase
from services.text_processing.ingest_processing.ingest_processing_base import IngestProcessingBase
from services.text_processing.text_utils import tiktoken_len


class IngestProcessingService(IngestProcessingBase):
    CLASS_NAME: str = "doc_ingest_processor_service"
    CLASS_UI_NAME: str = "Document Ingest Processor Service"
    REQUIRED_CLASSES: list[Type] = ingest_processing.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = ingest_processing.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_TYPINGS = ingest_processing.AVAILABLE_PROVIDERS_TYPINGS

    docs_token_counts: list[int] = []
    successfully_chunked_counter: int = 0

    def __init__(
        self,
        doc_ingest_processor_name: ingest_processing.AVAILABLE_PROVIDERS_TYPINGS,
        config_file_dict: dict[str, Any] = {},
        context_index_config: dict[str, Any] = {},
        **kwargs,
    ):
        super().__init__(
            current_provider_name=doc_ingest_processor_name,
            config_file_dict=config_file_dict,
            context_index_config=context_index_config,
            **kwargs,
        )
        if not self.current_provider_instance:
            raise ValueError("self.current_provider_instance not properly set!")

        self.current_doc_ingest_processor: IngestProcessingBase = self.current_provider_instance

    def create_chunks(
        self,
        text: str | dict,
    ) -> Optional[list[str]]:
        doc_chunks = self.current_doc_ingest_processor.create_chunks_with_provider(text=text)
        if not doc_chunks:
            self.log.info(f"{text[:10]} produced no chunks")
            return None

        self.log.info(f"{text[:10]} produced {len(doc_chunks)} chunks")

        return doc_chunks

    def preprocess_text(
        self,
        text: str,
    ) -> str:
        return self.current_doc_ingest_processor.preprocess_text_with_provider(text=text)

    def process_documents_from_context_index_source(
        self,
        ingest_docs: list[IngestDoc],
        source: doc_index_models.SourceModel,
    ) -> tuple[list[IngestDoc], list[str]]:
        preprocessed_docs = []
        for doc in ingest_docs:
            if isinstance(doc.precleaned_content, dict):
                raise ValueError("IngestDoc precleaned_content must be a string here.")
            doc.cleaned_content = self.preprocess_text(
                text=doc.precleaned_content,
            )
            doc.cleaned_content_token_count = text_utils.tiktoken_len(doc.cleaned_content)
            doc.hashed_cleaned_content = text_utils.hash_content(doc.cleaned_content)
            preprocessed_docs.append(doc)

        self.get_existing_docs_from_context_index_source(
            ingest_docs=preprocessed_docs, source=source
        )
        if not (docs_requiring_update := self.check_for_docs_requiring_update(preprocessed_docs)):
            self.log.info(f"No new data found for {source.name}")
            return [], []

        doc_db_ids_requiring_deletion: list[str] = []
        upsert_docs: list[IngestDoc] = []
        for doc in docs_requiring_update:
            self.log.info(f"Processing and chunking {doc.title}")
            if doc.cleaned_content is None:
                raise ValueError("doc.cleaned_content must not be None")
            text_chunks = self.create_chunks(
                text=doc.cleaned_content,
            )
            if not text_chunks:
                self.log.info(f"🔴 Skipping doc because text_chunks is None")
                continue
            doc_db_ids_requiring_deletion.extend(
                self.clear_and_get_existing_doc_db_chunks(ingest_doc=doc)
            )
            upsert_docs.append(
                self.create_document_and_chunk_models(
                    text_chunks=text_chunks, ingest_doc=doc, source=source
                )
            )
        if not upsert_docs:
            self.log.info(f"🔴 No new or post-processed documents for {source.name}")

        self.log.info(
            f"🟢 Total documents processed: {len(upsert_docs)}\n"
            f"Total document chunks: {self.successfully_chunked_counter}\n"
            f"Total tokens: {int(sum(self.docs_token_counts))}\n"
            f"Min chunk tokens: {min(self.docs_token_counts)}\n"
            f"Avg chunk tokens: {int(sum(self.docs_token_counts) / len(self.docs_token_counts))}\n"
            f"Max chunk tokens: {max(self.docs_token_counts)}"
        )

        return upsert_docs, doc_db_ids_requiring_deletion

    def clear_and_get_existing_doc_db_chunks(self, ingest_doc: IngestDoc) -> list[str]:
        doc_db_ids = []
        if not ingest_doc.existing_document_model:
            return []
        for chunk in ingest_doc.existing_document_model.context_chunks:
            doc_db_ids.append(chunk.id)
            self.session.flush()
            self.session.delete(chunk)
            self.session.flush()
        return doc_db_ids

    def create_document_and_chunk_models(
        self,
        text_chunks: list[str],
        ingest_doc: IngestDoc,
        source: doc_index_models.SourceModel,
    ) -> IngestDoc:
        if not ingest_doc.existing_document_model:
            ingest_doc.existing_document_model = doc_index_models.DocumentModel(
                source_id=source.id,
                cleaned_content=ingest_doc.cleaned_content,
                hashed_cleaned_content=ingest_doc.hashed_cleaned_content,
                title=ingest_doc.title,
                uri=ingest_doc.uri,
                batch_update_enabled=source.batch_update_enabled,
                source_type=ingest_doc.source_type,
                date_published=ingest_doc.date_published,
            )
            self.session.flush()
            source.documents.append(ingest_doc.existing_document_model)
            self.session.flush()
        for chunk in text_chunks:
            ingest_doc.existing_document_model.context_chunks.append(
                doc_index_models.ChunkModel(
                    context_chunk=chunk, chunk_doc_db_name=source.enabled_doc_db.name
                )
            )
            self.successfully_chunked_counter += 1
            self.session.flush()
        doc_token_count = [tiktoken_len(chunk) for chunk in text_chunks]
        self.docs_token_counts.extend(doc_token_count)
        self.log.info(
            f"🟢 Doc split into {len(text_chunks)} of averge length {int(sum(doc_token_count) / len(text_chunks))}"
        )

        return ingest_doc

    def check_for_docs_requiring_update(
        self, preprocessed_docs: list[IngestDoc]
    ) -> list[IngestDoc]:
        docs_requiring_update = []
        for doc in preprocessed_docs:
            if not doc.existing_document_model:
                docs_requiring_update.append(doc)
                continue
            if doc.hashed_cleaned_content != doc.existing_document_model.hashed_cleaned_content:
                docs_requiring_update.append(doc)

        self.log.info(f"{len(docs_requiring_update)} document requires update.")
        return docs_requiring_update

    def get_existing_docs_from_context_index_source(
        self,
        ingest_docs: list[IngestDoc],
        source: doc_index_models.SourceModel,
    ):
        existing_document_models = []
        for doc in ingest_docs:
            for document_model in source.documents:
                if doc.uri == document_model.uri:
                    doc.existing_document_id = document_model.id
                    doc.existing_document_model = document_model
                    existing_document_models.append(document_model)
                    break
            self.log.info(
                f"Found {len(existing_document_models)} existing documents for this source."
            )

    @classmethod
    def create_doc_index_ui_components(
        cls,
        parent_instance: doc_index_models.DomainModel | doc_index_models.SourceModel,
        groups_rendered: bool = True,
    ):
        provider_configs_dict = {}

        for provider in parent_instance.doc_loaders:
            name = provider.name
            config = provider.config
            provider_configs_dict[name] = config

        text_processing_provider_name = parent_instance.enabled_doc_ingest_processor.name

        provider_select_dd, service_providers_dict = GradioBase.abstract_service_ui_components(
            service_name=cls.CLASS_NAME,
            enabled_provider_name=text_processing_provider_name,
            required_classes=cls.REQUIRED_CLASSES,
            provider_configs_dict=provider_configs_dict,
            groups_rendered=groups_rendered,
        )

        return provider_select_dd, service_providers_dict
