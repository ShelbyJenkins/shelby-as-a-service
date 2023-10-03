# region

from typing import Any, Generator, List, Optional
from urllib.parse import urlparse, urlunparse

import gradio as gr
import modules.prompt_templates as PromptTemplates
import modules.text_processing.text as text
import modules.utils.config_manager as ConfigManager
from agents.agent_base import AgentBase
from agents.ingest_agent import IngestAgent
from services.llm_service import LLMService

# endregion


class WebAgent(AgentBase):
    agent_name: str = "web_agent"
    agent_ui_name: str = "URL Agent"
    agent_select_status_message: str = (
        "Load a URL Data Tab, and we'll access it and use it to generate a response."
    )
    default_prompt_template_path: str = "web_prompt.yaml"
    app: Optional[Any] = None
    index: Optional[Any] = None
    database_provider: str = "local_filestore_database"

    def __init__(self, parent_sprite=None):
        super().__init__(parent_sprite=parent_sprite)

        self.ingest_agent = IngestAgent(parent_sprite)

        self.llm_service = LLMService(self)

    def create_streaming_chat(
        self,
        query,
        user_prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ) -> Generator[List[str], None, None]:
        self.log.print_and_log(f"Running query: {query}")

        if user_prompt_template_path:
            prompt_template_path = user_prompt_template_path
        else:
            prompt_template_path = self.default_prompt_template_path

        self.log.print_and_log("Sending prompt to LLM")
        yield from self.llm_service.create_streaming_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

    def create_chat(
        self,
        query,
        user_prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ) -> Optional[str]:
        self.log.print_and_log(f"Running query: {query}")

        if user_prompt_template_path:
            prompt_template_path = user_prompt_template_path
        else:
            prompt_template_path = self.default_prompt_template_path

        self.log.print_and_log("Sending prompt to LLM")
        return self.llm_service.create_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

    def load_single_website(self, comps_state):
        if web_tab_url_text := comps_state.get("web_tab_url_text", None):
            try:
                parsed_url = urlparse(web_tab_url_text)
                complete_url = urlunparse(parsed_url)
                documents = self.ingest_agent.load_single_website(complete_url)
                output = ""
                if documents:
                    for document in documents:
                        if content := text.get_document_content(document):
                            output += content
                    return [output, output]

            except ValueError:
                pass
        raise gr.Error("Bad value for web_tab_url_text!")
