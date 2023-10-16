from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
import services.text_processing.text as text
from app_config.module_base import ModuleBase
from pydantic import BaseModel
from services.embedding.embedding_openai import OpenAIEmbedding


class EmbeddingService(ModuleBase):
    MODULE_NAME: str = "embedding_service"
    MODULE_UI_NAME: str = "embedding_service"
    PROVIDERS_TYPE: str = "embedding_providers"
    REQUIRED_MODULES: List[Type] = [OpenAIEmbedding]

    class ModuleConfigModel(BaseModel):
        agent_select_status_message: str = "Search index to find docs related to request."
        embedding_provider: str = "openai_embedding"

    config: ModuleConfigModel
    embedding_providers: List[Any]

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(
            module_instance=self, config_file_dict=config_file_dict, **kwargs
        )

    def get_query_embedding(self, query):
        provider = self.get_requested_module_instance(self.embedding_providers, "openai_embedding")
        if provider:
            return provider._get_query_embedding(query)
        return None

    def get_documents_embedding(self, query):
        provider = self.get_requested_module_instance(self.embedding_providers, "openai_embedding")
        if provider:
            return provider._get_documents_embedding(query)
        return None

    def create_settings_ui(self):
        components = {}

        pass

        return components
