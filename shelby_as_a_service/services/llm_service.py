from typing import Any, Dict, List, Optional, Type

from app.app_base import AppBase
from pydantic import BaseModel
from services.providers.llm_openai import OpenAILLM
from services.service_base import ServiceBase


class LLMService(ServiceBase):
    SERVICE_NAME: str = "llm_service"
    SERVICE_UI_NAME: str = "llm_service"
    PROVIDER_TYPE: str = "llm_provider"
    DEFAULT_PROVIDER: Type = OpenAILLM
    AVAILABLE_PROVIDERS: List[Type] = [OpenAILLM]

    class ServiceConfigModel(BaseModel):
        agent_select_status_message: str = (
            "Search index to find docs related to request."
        )
        max_response_tokens: int = 300

    def __init__(self):
        super().__init__()

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
