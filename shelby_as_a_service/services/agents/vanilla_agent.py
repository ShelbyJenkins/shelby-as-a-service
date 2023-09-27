# region
import os

import json, yaml
from services.utils.app_base import AppBase
from services.utils.log_service import Logger
from services.providers.llm_service import LLMService


# endregion


class VanillaChatAgent(AppBase):

    llm_provider: str = "openai_llm"
    # main_prompt_llm_model: str = "gpt-4"
    main_prompt_llm_model: str = None

    max_response_tokens: int = 300

    def __init__(self, config_path):
        super().__init__(
            service_name_="vanilla_agent",
            required_variables_=["docs_to_retrieve"],
            config_path=config_path,
        )


        self.llm_service = LLMService(
            enabled_provider=self.llm_provider,
            enabled_model=self.main_prompt_llm_model,
        )

        self.log = Logger(
            AppBase.app_name,
            "VanillaChatAgent",
            "vanilla_agent.md",
            level="INFO",
        )
        
    def run_query(self, query):
    
        self.log.print_and_log(f"Running query: {query}")

        prompt = self._create_prompt_template(query)

        self.log.print_and_log("Sending prompt to LLM")
        llm_response = self.llm_service.create_streaming_chat(prompt)

        return llm_response
    
    def _create_prompt_template(self, query):
        with open(
            os.path.join(
                "shelby_as_a_service/models/prompt_templates/", "vanilla_prompt.yaml"
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