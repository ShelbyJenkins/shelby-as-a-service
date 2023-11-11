from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from services.agents import AVAILABLE_AGENT_NAMES, AVAILABLE_AGENT_UI_NAMES, AVAILABLE_AGENTS
from services.service_base import ServiceBase


class AgentService(ABC, ServiceBase):
    CLASS_NAME: str = "agent_service"
    CLASS_UI_NAME: str = "Agent Service"
    AVAILABLE_AGENTS: list[Type] = AVAILABLE_AGENTS
    AVAILABLE_AGENT_UI_NAMES: list[str] = AVAILABLE_AGENT_UI_NAMES
    AVAILABLE_AGENT_NAMES = AVAILABLE_AGENT_NAMES

    def prep_chat(
        self, query, llm_model_name: Optional[str] = None
    ) -> tuple[list[dict[str, str]], "ModelConfig", int]:
        llm_model = self.get_model(requested_model_name=llm_model_name)

        prompt = PromptTemplates.create_openai_prompt(
            query=query,
            prompt_template_path=prompt_template_path,
        )

        total_prompt_tokens = text_utils.tiktoken_len_of_openai_prompt(prompt, llm_model)

        if prompt is None or llm_model is None or total_prompt_tokens is None:
            raise ValueError(
                f"Error with input values - prompt: {prompt}, model: {llm_model}, total_prompt_tokens: {total_prompt_tokens}"
            )
        return prompt, llm_model, total_prompt_tokens
