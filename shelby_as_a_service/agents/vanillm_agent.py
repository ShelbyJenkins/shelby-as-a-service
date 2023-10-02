# region
import json
from typing import Any, Dict, List, Optional

import modules.prompt_templates as PromptTemplates
import modules.utils.config_manager as ConfigManager
from agents.agent_base import AgentBase
from modules.utils.get_app import get_app
from services.llm_service import LLMService

# endregion


class VanillaLLM(AgentBase):
    agent_name: str = "vanillallm_agent"
    default_prompt_template_path: str = "vanillallm_prompt.yaml"

    llm_provider: str = "openai_llm"
    llm_model: str = "gpt-4"

    def __init__(self, parent_sprite=None):
        self.app = get_app()
        super().__init__(parent_sprite=parent_sprite)
        ConfigManager.setup_service_config(self)

        self.llm_service = LLMService(self)

    def create_streaming_chat(
        self,
        query,
        user_prompt_template_path=None,
        documents=None,
        provider_name=None,
        model_name=None,
    ):
        self.log.print_and_log(f"Running query: {query}")

        prompt_template = PromptTemplates.load_prompt_template(
            self.default_prompt_template_path, user_prompt_template_path
        )

        self.log.print_and_log("Sending prompt to LLM")
        yield from self.llm_service.create_streaming_chat(
            query=query,
            prompt_template=prompt_template,
            documents=documents,
            provider_name=provider_name,
            model_name=model_name,
        )

    def create_chat(
        self,
        query,
        user_prompt_template_path=None,
        documents=None,
        provider_name=None,
        model_name=None,
    ):
        self.log.print_and_log(f"Running query: {query}")

        prompt_template = PromptTemplates.load_prompt_template(
            self.default_prompt_template_path, user_prompt_template_path
        )

        self.log.print_and_log("Sending prompt to LLM")
        return self.llm_service.create_streaming_chat(
            query=query,
            prompt_template=prompt_template,
            documents=documents,
            provider_name=provider_name,
            model_name=model_name,
        )
