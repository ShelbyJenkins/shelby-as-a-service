from typing import Any, Dict, Generator, List, Optional, Type, Union

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

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(
            module_instance=self,
            config_file_dict=config_file_dict,
            llm_provider="openai_llm",
            model="gpt-4",
            **kwargs,
        )

    def run_chat(self, chat_in):
        response = self.llm_service.create_chat(
            query=chat_in,
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
        )
        yield from response

    def create_settings_ui(self):
        pass
