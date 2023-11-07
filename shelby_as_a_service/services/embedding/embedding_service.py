import typing
from abc import ABC, abstractmethod
from typing import Any, Final, Iterator, Literal, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
from app.module_base import ModuleBase
from langchain.schema import Document

from . import AVAILABLE_PROVIDERS, AVAILABLE_PROVIDERS_NAMES, AVAILABLE_PROVIDERS_UI_NAMES


class EmbeddingService(ABC, ModuleBase):
    CLASS_NAME: str = "embedding_service"
    CLASS_UI_NAME: str = "Embedding Service"
    REQUIRED_CLASSES: list[Type] = AVAILABLE_PROVIDERS
    LIST_OF_CLASS_NAMES: list[str] = list(typing.get_args(AVAILABLE_PROVIDERS_NAMES))
    LIST_OF_CLASS_UI_NAMES: list[str] = AVAILABLE_PROVIDERS_UI_NAMES
    AVAILABLE_PROVIDERS_NAMES = AVAILABLE_PROVIDERS_NAMES

    @classmethod
    def get_document_embeddings_from_provider(
        cls,
        docs: list[Document],
        provider_name: AVAILABLE_PROVIDERS_NAMES,
        provider_config: dict[str, Any] = {},
        **kwargs,
    ) -> list[Document]:
        provider: Type[EmbeddingService] = cls.get_requested_class(
            requested_class=provider_name, available_classes=cls.REQUIRED_CLASSES
        )

        for doc in docs:
            embedding = provider(config_file_dict=provider_config, **kwargs).get_embedding(
                content=doc.page_content
            )
            if embedding:
                doc.metadata["embedding"] = embedding
            else:
                raise Exception("No embedding found")
        return docs

    @abstractmethod
    def get_embedding(self, content: str, model_name: Optional[str] = None) -> list[float]:
        raise NotImplementedError

    def create_settings_ui(self):
        components = {}

        components["embedding_provider"] = gr.Dropdown(
            value=GradioHelpers.get_class_ui_name_from_str(
                self.list_of_required_class_instances, self.config.embedding_provider
            ),
            choices=GradioHelpers.get_list_of_class_ui_names(self.list_of_required_class_instances),
            label=self.CLASS_UI_NAME,
            container=True,
            min_width=0,
        )

        for provider_instance in self.list_of_required_class_instances:
            provider_instance.create_settings_ui()

        GradioHelpers.create_settings_event_listener(self.config, components)

        return components
