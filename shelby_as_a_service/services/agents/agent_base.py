from typing import Annotated, Any, Generator, Literal, Optional, Type, get_args

import services.llm as llm
import services.text_processing.prompts.prompt_template_service as prompts
from services.service_base import ServiceBase


class AgentBase(ServiceBase):
    def create_prompt(
        self,
        query,
        prompt_template_path: str,
        llm_provider_name: llm.AVAILABLE_PROVIDERS_NAMES,
        context_docs: Optional[list[dict]] = None,
    ) -> list[dict[str, str]]:
        if llm_provider_name == llm.OpenAILLM.CLASS_NAME:
            return prompts.create_openai_prompt(
                query=query,
                prompt_template_path=prompt_template_path,
                context_docs=context_docs,
            )
        else:
            raise ValueError(f"llm_provider_name {llm_provider_name} not found.")
