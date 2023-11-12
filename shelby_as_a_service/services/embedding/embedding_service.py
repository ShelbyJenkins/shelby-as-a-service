from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
import services.embedding as embedding
from services.embedding.embedding_base import EmbeddingBase


class EmbeddingService(EmbeddingBase):
    CLASS_NAME: str = "embedding_service"

    CLASS_UI_NAME: str = "Embedding Service"
    REQUIRED_CLASSES: list[Type] = embedding.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = embedding.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = embedding.AVAILABLE_PROVIDERS_NAMES
    list_of_embedding_provider_instances: list[EmbeddingBase] = []
    current_embedding_provider: EmbeddingBase

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.list_of_embedding_provider_instances = self.list_of_required_class_instances
        embedding_provider_name = kwargs.get("embedding_provider_name", None)
        if embedding_provider_name:
            self.current_embedding_provider = self.get_requested_class_instance(
                requested_class=embedding_provider_name,
                available_classes=self.list_of_embedding_provider_instances,
            )

    def get_embedding_instance(
        self,
        embedding_provider_name: Optional[embedding.AVAILABLE_PROVIDERS_NAMES] = None,
        embedding_instance: Optional[EmbeddingBase] = None,
    ) -> EmbeddingBase:
        if embedding_provider_name and embedding_instance:
            raise ValueError(
                "Must provide either embedding_provider_name or embedding_instance, not both."
            )
        if embedding_provider_name:
            embedding = self.get_requested_class_instance(
                requested_class=embedding_provider_name,
                available_classes=self.list_of_embedding_provider_instances,
            )
        elif embedding_instance:
            embedding = embedding_instance
        else:
            embedding = self.current_embedding_provider
        if embedding is None:
            raise ValueError("embedding must not be None")
        return embedding

    def get_embedding_of_text(
        self,
        text: str,
        model_name: Optional[str] = None,
        embedding_provider_name: Optional[embedding.AVAILABLE_PROVIDERS_NAMES] = None,
        embedding_instance: Optional[EmbeddingBase] = None,
    ) -> list[float]:
        embedding = self.get_embedding_instance(
            embedding_provider_name=embedding_provider_name,
            embedding_instance=embedding_instance,
        )

        text_embedding = embedding.get_embedding_of_text(text=text, model_name=model_name)
        if text_embedding is None:
            raise ValueError("No embedding returned")
        return text_embedding

    def get_embeddings_from_list_of_texts(
        self,
        texts: list[str],
        model_name: Optional[str] = None,
        embedding_provider_name: Optional[embedding.AVAILABLE_PROVIDERS_NAMES] = None,
        embedding_instance: Optional[EmbeddingBase] = None,
    ) -> list[list[float]]:
        embedding = self.get_embedding_instance(
            embedding_provider_name=embedding_provider_name,
            embedding_instance=embedding_instance,
        )
        text_embeddings = embedding.get_embeddings_from_list_of_texts(
            texts=texts, model_name=model_name
        )
        if text_embeddings is None:
            raise ValueError("No embeddings returned")
        self.log.info(f"Got {len(text_embeddings)} embeddings")
        return text_embeddings

    def get_document_embeddings_for_chunks_to_upsert(
        self,
        chunks_to_upsert: list[doc_index_models.ChunkModel],
        doc_index_db_model: doc_index_models.DocDBModel,
    ):
        doc_index_embedding_instance: EmbeddingBase = self.init_provider_instance_from_doc_index(
            doc_index_db_model=doc_index_db_model
        )
        upsert_chunks_text = []
        upsert_docs_text_embeddings = []
        for chunk in chunks_to_upsert:
            upsert_chunks_text.append(chunk.context_chunk)

        upsert_docs_text_embeddings = self.get_embeddings_from_list_of_texts(
            texts=upsert_chunks_text,
            embedding_instance=doc_index_embedding_instance,
        )
        if len(upsert_docs_text_embeddings) != len(upsert_chunks_text):
            raise ValueError("Number of embeddings does not match number of context chunks")

        for i, chunk in enumerate(chunks_to_upsert):
            chunk.chunk_embedding = upsert_docs_text_embeddings[i]
