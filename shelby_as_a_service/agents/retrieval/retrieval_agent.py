from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.module_base import ModuleBase
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.embedding.embedding_service import EmbeddingService


class RetrievalAgent(ModuleBase):
    MODULE_NAME: str = "retrieval_agent"
    MODULE_UI_NAME: str = "Retrieval Agent"

    REQUIRED_MODULES: List[Type] = [EmbeddingService, DatabaseService]

    class ModuleConfigModel(BaseModel):
        database_provider: str = "local_filestore_database"

    config: ModuleConfigModel
    embeddings_service: EmbeddingService
    database_service: DatabaseService

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            for module_instance in self.list_of_module_instances:
                with gr.Tab(label=module_instance.MODULE_UI_NAME):
                    module_instance.create_settings_ui()

            GradioHelper.create_settings_event_listener(self, components)

        return components
