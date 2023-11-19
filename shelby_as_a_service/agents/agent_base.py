from typing import Annotated, Any, Generator, Literal, Optional, Type, get_args

import services.llm as llm
import services.text_processing.prompts.prompt_template_service as prompts
from context_index.doc_index.docs.context_docs import RetrievalDoc
from pydantic import BaseModel
from services.llm.llm_service import LLMService
from services.service_base import ServiceBase


class ClassConfigModel(BaseModel):
    pass

    class Config:
        extra = "ignore"


class AgentBase(ServiceBase):
    config: ClassConfigModel
    llm_service: LLMService

    @staticmethod
    def create_prompt(
        llm_provider_name: llm.AVAILABLE_PROVIDERS_TYPINGS,  # type: ignore
        user_input: Optional[str] = None,
        prompt_template_path: Optional[str] = None,
        prompt_string: Optional[str] = None,
        context_docs: Optional[list[RetrievalDoc] | list[str] | str] = None,
    ) -> list[dict[str, str]]:
        if not prompt_string and not prompt_template_path:
            raise ValueError("prompt_string and prompt_template_path cannot both be None.")
        if llm_provider_name == llm.OpenAILLM.CLASS_NAME:
            return prompts.create_openai_prompt(
                user_input=user_input,
                prompt_string=prompt_string,
                prompt_template_path=prompt_template_path,
                context_docs=context_docs,
            )
        else:
            raise ValueError(f"llm_provider_name {llm_provider_name} not found.")
