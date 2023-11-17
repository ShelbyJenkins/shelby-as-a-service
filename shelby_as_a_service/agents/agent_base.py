from typing import Annotated, Any, Generator, Literal, Optional, Type, get_args

import services.llm as llm
import services.text_processing.prompts.prompt_template_service as prompts
from context_index.doc_index.docs.context_docs import RetrievalDoc
from services.service_base import ServiceBase


class AgentBase(ServiceBase):
    @staticmethod
    def create_prompt(
        query,
        prompt_template_path: str,
        llm_provider_name: llm.AVAILABLE_PROVIDERS_TYPINGS,
        context_docs: Optional[list[RetrievalDoc]] = None,
    ) -> list[dict[str, str]]:
        if llm_provider_name == llm.OpenAILLM.CLASS_NAME:
            return prompts.create_openai_prompt(
                query=query,
                prompt_template_path=prompt_template_path,
                context_docs=context_docs,
            )
        else:
            raise ValueError(f"llm_provider_name {llm_provider_name} not found.")
