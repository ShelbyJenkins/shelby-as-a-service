# region
import os

import json, yaml, re
from typing import Dict, Optional, List, Any

from agents.agent_base import AgentBase
import modules.utils.config_manager as ConfigManager
from agents.ingest_agent import IngestAgent
from services.llm_service import LLMService
import modules.text_processing.text as text
import sprites.web.interface_helpers as help
import modules.utils.config_manager as ConfigManager

# endregion


class WebAgent(AgentBase):
    agent_name: str = "web_agent"
    app: Optional[Any] = None
    index: Optional[Any] = None

    def __init__(self, parent_sprite=None):
        super().__init__(parent_sprite=parent_sprite)
        ConfigManager.setup_service_config(self)

        self.ingest_agent = IngestAgent(parent_sprite)

        self.llm_service = LLMService(self)

    def load_single_website(self, ui, *comps_state):
        state_dict = help.comp_values_to_dict(ui, *comps_state)
        documents = self.ingest_agent.load_single_website(state_dict)
        output = ""
        for document in documents:
            output += document.page_content
        return [output, output]

    def run_chat(self, ui, *comps_state):
        state_dict = help.comp_values_to_dict(ui, *comps_state)

        prompt = self._create_prompt_template(
            state_dict["chat_tab_in_text"], state_dict["web_data_content"]
        )

        yield from self.llm_service.create_streaming_chat(
            prompt,
            provider_name=state_dict["chat_llm_provider"],
            model_name=state_dict["chat_llm_model"],
        )

    def _create_prompt_template(self, query, web_data):
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

        prompt_template[1]["content"] = f"Supporting Docs: {web_data} fQuery: {query} "

        # self.log.print_and_log(f"prepared prompt: {json.dumps(prompt_template, indent=4)}")

        return prompt_template
