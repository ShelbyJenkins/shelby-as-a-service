# region
import json
from typing import Any, Dict, Generator, List, Optional

import modules.prompt_templates as PromptTemplates
from agents.agent_base import AgentBase
from app_base import AppBase
from pydantic import BaseModel
from services.llm_service import LLMService


# endregion
class AgentConfig(BaseModel):
    agent_select_status_message: str = "EZPZ"
    llm_provider: str = "openai_llm"
    llm_model: str = "gpt-4"


class VanillaLLM(AgentBase):
    AGENT_NAME: str = "vanillallm_agent"
    AGENT_UI_NAME: str = "VanillaLLM Agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "vanillallm_prompt.yaml"

    def __init__(self, parent_class=None):
        super().__init__(parent_class=parent_class)
        self.config = AppBase.load_service_config(
            class_instance=self, config_class=AgentConfig
        )

        self.llm_service = LLMService(self)

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
