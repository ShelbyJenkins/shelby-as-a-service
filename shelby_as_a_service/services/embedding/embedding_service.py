from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
import services.embedding as embedding
from services.embedding.embedding_base import EmbeddingBase


class EmbeddingService(EmbeddingBase):
    CLASS_NAME: str = "embedding_service"

    CLASS_UI_NAME: str = "Embedding Service"
    REQUIRED_CLASSES: list[Type] = embedding.AVAILABLE_PROVIDERS
    AVAILABLE_PROVIDERS_UI_NAMES: list[str] = embedding.AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_TYPINGS = embedding.AVAILABLE_PROVIDERS_TYPINGS

    def __init__(
        self,
        embedding_provider_name: embedding.AVAILABLE_PROVIDERS_TYPINGS,
        embedding_provider_model_name: Optional[str] = None,
        context_index_config: dict[str, Any] = {},
        config_file_dict: dict[str, Any] = {},
        **kwargs,
    ):
        if not embedding_provider_model_name:
            embedding_provider_model_name = context_index_config.get("current_embedding_model_name")

        super().__init__(
            current_provider_name=embedding_provider_name,
            provider_model_name=embedding_provider_model_name,
            context_index_config=context_index_config,
            config_file_dict=config_file_dict,
            **kwargs,
        )

        if not self.current_provider_instance:
            raise ValueError("current_provider_instance not properly set!")

        self.current_embedder_provider: EmbeddingBase = self.current_provider_instance

    def get_embedding_of_text(
        self,
        text: str,
    ) -> list[float]:
        text_embedding = self.current_embedder_provider.get_embedding_of_text_with_provider(
            text=text
        )
        if text_embedding is None:
            raise ValueError("No embedding returned")
        return text_embedding

    def get_embeddings_from_list_of_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        text_embeddings = (
            self.current_embedder_provider.get_embeddings_from_list_of_texts_with_provider(
                texts=texts
            )
        )
        if text_embeddings is None:
            raise ValueError("No embeddings returned")
        self.log.info(f"Got {len(text_embeddings)} embeddings")
        return text_embeddings

    def get_document_embeddings_for_chunks_to_upsert(
        self,
        chunks_to_upsert: list[doc_index_models.ChunkModel],
    ):
        upsert_chunks_text = []
        upsert_docs_text_embeddings = []
        for chunk in chunks_to_upsert:
            upsert_chunks_text.append(chunk.context_chunk)

        upsert_docs_text_embeddings = self.get_embeddings_from_list_of_texts(
            texts=upsert_chunks_text,
        )
        if len(upsert_docs_text_embeddings) != len(upsert_chunks_text):
            raise ValueError("Number of embeddings does not match number of context chunks")

        for i, chunk in enumerate(chunks_to_upsert):
            chunk.chunk_embedding = upsert_docs_text_embeddings[i]
