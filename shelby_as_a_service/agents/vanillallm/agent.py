from typing import Any, Dict, Generator, List, Optional, Type

import gradio as gr
import sprites.webui.gradio_helpers as GradioHelper
from agents.agent_base import AgentBase
from agents.vanillallm.ui import VanillaLLMUI
from pydantic import BaseModel
from services.llm_service import LLMService


class VanillaLLM(AgentBase):
    AGENT_NAME: str = "vanillallm_agent"
    AGENT_UI_NAME: str = "VanillaLLM Agent"
    AGENT_UI = VanillaLLMUI
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "vanillallm_prompt.yaml"
    AVAILABLE_SERVICES: List[Type] = [LLMService]

    class AgentConfigModel(BaseModel):
        agent_select_status_message: str = "EZPZ"
        llm_provider: str = "openai_llm"
        llm_model: str = "gpt-4"

        class Config:
            extra = "ignore"

    config: AgentConfigModel

    def __init__(self, config_dict_from_file: Optional[Dict[str, Any]] = None, **kwargs):
        self.config_dict_from_file = config_dict_from_file or {}
        self.config = self.AgentConfigModel(**{**kwargs, **self.config_dict_from_file})
        self.services_config_dict_from_file = self.config_dict_from_file.get("services", {})
        super().__init__()
        self.config_dict_from_file.update(self.config.model_dump())

        self.llm_service = LLMService(
            self.services_config_dict_from_file.get("llm_service", {}),
            llm_provider=self.config.llm_provider,
            llm_model=self.config.llm_model,
            **kwargs,
        )

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
