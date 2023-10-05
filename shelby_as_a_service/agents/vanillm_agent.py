# region
import json
from typing import Any, Dict, Generator, List, Optional, Type

import modules.prompt_templates as PromptTemplates
from agents.agent_base import AgentBase
from app.app_base import AppBase
from pydantic import BaseModel
from services.llm_service import LLMService

# endregion


class VanillaLLM(AgentBase):
    AGENT_NAME: str = "vanillallm_agent"
    AGENT_UI_NAME: str = "VanillaLLM Agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "vanillallm_prompt.yaml"
    AVAILABLE_SERVICES: List[Type] = [LLMService]

    class AgentConfigModel(BaseModel):
        agent_select_status_message: str = "EZPZ"
        llm_provider: str = "openai_llm"
        llm_model: str = "gpt-4"

    def __init__(self):
        super().__init__()

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
