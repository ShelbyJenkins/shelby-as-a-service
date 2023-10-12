from typing import Any, Dict, Generator, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from agents.agent_base import AgentBase
from agents.vanillallm.vanillallm_ui import VanillaLLMUI
from pydantic import BaseModel
from services.llm.llm_service import LLMService


class VanillaLLM(AgentBase):
    MODULE_NAME: str = "vanillallm_agent"
    AGENT_UI = VanillaLLMUI
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "vanillallm_prompt.yaml"
    REQUIRED_MODULES: List[Type] = [LLMService]

    class AgentConfigModel(BaseModel):
        agent_select_status_message: str = "EZPZ"
        llm_provider: str = "openai_llm"
        llm_model: str = "gpt-4"

        class Config:
            extra = "ignore"

    config: AgentConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        # super().__init__()
        module_config_file_dict = config_file_dict.get(self.MODULE_NAME, {})
        self.config = self.AgentConfigModel(**{**kwargs, **module_config_file_dict})

        self.llm_service = LLMService(module_config_file_dict)

    def create_streaming_chat(
        self,
        query,
        user_prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ) -> Generator[List[str], None, None]:
        self.log.print_and_log(f"Running query: {query}")
        if user_prompt_template_path:
            prompt_template_path = user_prompt_template_path
        else:
            prompt_template_path = self.DEFAULT_PROMPT_TEMPLATE_PATH

        self.log.print_and_log("Sending prompt to LLM")
        yield from self.llm_service.create_streaming_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

    def create_chat(
        self,
        query,
        user_prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ) -> Optional[str]:
        self.log.print_and_log(f"Running query: {query}")
        if user_prompt_template_path:
            prompt_template_path = user_prompt_template_path
        else:
            prompt_template_path = self.DEFAULT_PROMPT_TEMPLATE_PATH

        self.log.print_and_log("Sending prompt to LLM")
        return self.llm_service.create_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )
