from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
import services.text_processing.text as text
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.embedding.embedding_openai import OpenAIEmbedding


class EmbeddingService(ModuleBase):
    CLASS_NAME: str = "embedding_service"
    CLASS_UI_NAME: str = "Embeddings"
    REQUIRED_CLASSES: List[Type] = [OpenAIEmbedding]

    class ClassConfigModel(BaseModel):
        embedding_provider: str = "openai_embedding"

    config: ClassConfigModel
    list_of_class_instances: list[Any]
    list_of_class_ui_names: list

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

    def get_query_embedding(self, query) -> list[float]:
        provider = self.get_requested_class_instance(self.list_of_class_instances, "openai_embedding")
        # provider = self.get_requested_class_instance(
        #     self.list_of_class_instances, embedding_provider if embedding_provider is not None else self.config.embedding_provider
        # )
        if provider:
            return provider.get_query_embedding(query)
        return None

    def get_documents_embedding(self, query) -> list[list[float]]:
        provider = self.get_requested_class_instance(self.list_of_class_instances, "openai_embedding")
        if provider:
            return provider.get_documents_embedding(query)
        return None

    def create_settings_ui(self):
        components = {}

        components["embedding_provider"] = gr.Dropdown(
            value=GradioHelper.get_class_ui_name_from_str(self.list_of_class_instances, self.config.embedding_provider),
            choices=GradioHelper.get_list_of_class_ui_names(self.list_of_class_instances),
            label=self.CLASS_UI_NAME,
            container=True,
            min_width=0,
        )

        for provider_instance in self.list_of_class_instances:
            provider_instance.create_settings_ui()

        GradioHelper.create_settings_event_listener(self.config, components)

        return components
