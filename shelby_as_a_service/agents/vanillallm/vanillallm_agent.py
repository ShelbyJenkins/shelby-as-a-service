from typing import Any, Dict, Generator, List, Optional, Type, Union

import gradio as gr
from app_config.module_base import ModuleBase
from pydantic import BaseModel
from services.llm.llm_service import LLMService


class VanillaLLM(ModuleBase):
    MODULE_NAME: str = "vanillallm_agent"
    MODULE_UI_NAME = "VanillaLLM Agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "agents/vanillallm/vanillallm_prompt_templates.yaml"
    REQUIRED_MODULES: List[Type] = [LLMService]

    class ModuleConfigModel(BaseModel):
        agent_select_status_message: str = "EZPZ"

        class Config:
            extra = "ignore"

    config: ModuleConfigModel
    llm_service: LLMService
    list_of_module_instances: list

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(
            module_instance=self,
            config_file_dict=config_file_dict,
            llm_provider="openai_llm",
            model="gpt-4",
            **kwargs,
        )

    def run_chat(self, chat_in):
        for response in self.llm_service.create_chat(
            query=chat_in,
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
        ):
            yield response["response_content_string"]

    def create_settings_ui(self):
        for module_instance in self.list_of_module_instances:
            with gr.Tab(label=module_instance.MODULE_UI_NAME):
                module_instance.create_settings_ui()
