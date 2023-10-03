from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type

import modules.prompt_templates as PromptTemplates
import modules.text_processing.text as TextProcess
import modules.utils.config_manager as ConfigManager
import openai
from modules.utils.log_service import Logger
from pydantic import Field
from services.providers.llm_openai import OpenAILLM
from services.service_base import ServiceBase


class LLMService(ServiceBase):
    service_name: str = "llm_service"
    service_ui_name: str = "llm_service"
    provider_type: str = "llm_provider"
    available_providers: List[Type] = [OpenAILLM]
    default_provider: Type = OpenAILLM

    max_response_tokens: int = 300

    def __init__(self, parent_agent):
        super().__init__(parent_agent=parent_agent)

    def create_streaming_chat(
        self,
        query,
        prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ):
        provider = self.get_provider(new_provider_name=llm_provider)
        if provider:
            yield from provider._create_streaming_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                documents=documents,
                llm_model=llm_model,
            )

    def create_chat(
        self,
        query,
        prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ) -> Optional[str]:
        provider = self.get_provider(new_provider_name=llm_provider)
        if provider:
            return provider._create_chat(
                query=query,
                prompt_template_path=prompt_template_path,
                documents=documents,
                llm_model=llm_model,
            )
        return None
