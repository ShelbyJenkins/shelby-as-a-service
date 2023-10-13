import types
from typing import Any, Dict, Generator, List, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from agents.vanillallm.vanillallm_ui import VanillaLLMUI
from app_config.app_base import AppBase
from pydantic import BaseModel
from services.llm.llm_service import LLMService


class VanillaLLM(AppBase):
    MODULE_NAME: str = "vanillallm_agent"
    MODULE_UI = VanillaLLMUI
    MODULE_UI_NAME: str = VanillaLLMUI.MODULE_UI_NAME
    DEFAULT_PROMPT_TEMPLATE_PATH: str = (
        "shelby_as_a_service/agents/vanillallm/vanillallm_prompt_templates.yaml"
    )
    REQUIRED_MODULES: List[Type] = [LLMService]

    class ModuleConfigModel(BaseModel):
        agent_select_status_message: str = "EZPZ"

        class Config:
            extra = "ignore"

    config: ModuleConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        module_config_file_dict = config_file_dict.get(self.MODULE_NAME, {})
        self.config = self.ModuleConfigModel(**{**kwargs, **module_config_file_dict})

        self.llm_service = LLMService(
            module_config_file_dict, llm_provider="openai_llm", model="gpt-4"
        )

        self.required_module_instances = self.get_list_of_module_instances(
            self, self.REQUIRED_MODULES
        )

    def run_chat(self, chat_in) -> Generator[List[str], None, None]:
        self.log.print_and_log(f"Running query: {chat_in}")

        response = self.llm_service.create_chat(
            query=chat_in,
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
        )
        yield from response
