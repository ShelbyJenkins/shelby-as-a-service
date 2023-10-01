# region
import os

import json, yaml
from typing import Dict, Optional, List, Any

from modules.utils.log_service import Logger
from services.llm_service import LLMService
from agents.agent_base import AgentBase
import modules.utils.config_manager as ConfigManager

# endregion


class VanillaChatAgent(AgentBase):
    agent_name: str = "vanilla_agent"
    app: Optional[Any] = None
    index: Optional[Any] = None

    llm_provider: str = "openai_llm"
    llm_model: str = "gpt-4"

    def __init__(self, parent_sprite=None):
        super().__init__(parent_sprite=parent_sprite)
        ConfigManager.setup_service_config(self)

        self.llm_service = LLMService(self)

    def create_streaming_chat(
        self, query, stream=False, provider_name=None, model_name=None
    ):
        self.log.print_and_log(f"Running query: {query}")

        prompt = self._create_prompt_template(query)

        self.log.print_and_log("Sending prompt to LLM")
        if stream:
            yield from self.llm_service.create_streaming_chat(
                prompt,
                provider_name=provider_name
                if provider_name is not None
                else self.llm_provider,
                model_name=model_name if model_name is not None else self.llm_model,
            )
        else:
            return self.llm_service.create_chat(
                prompt,
                provider_name=provider_name
                if provider_name is not None
                else self.llm_provider,
                model_name=model_name if model_name is not None else self.llm_model,
            )

    def _create_prompt_template(self, query):
        with open(
            os.path.join(
                "shelby_as_a_service/modules/prompt_templates/", "vanilla_prompt.yaml"
            ),
            "r",
            encoding="utf-8",
        ) as stream:
            # Load the YAML data and print the result
            prompt_template = yaml.safe_load(stream)

        # Loop over documents and append them to each other and then adds the query

        prompt_template[1]["content"] = f"Query: {query}"

        # self.log.print_and_log(f"prepared prompt: {json.dumps(prompt_template, indent=4)}")

        return prompt_template
