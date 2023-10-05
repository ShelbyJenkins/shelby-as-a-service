# region

from typing import Any, Generator, List, Optional
from urllib.parse import urlparse, urlunparse

import gradio as gr
import modules.prompt_templates as PromptTemplates
import modules.text_processing.text as text
import modules.utils.config_manager as ConfigManager
from agents.agent_base import AgentBase
from agents.ingest_agent import IngestAgent
from app.app_base import AppBase
from pydantic import BaseModel
from services.llm_service import LLMService


# endregion
#
class AgentConfig(BaseModel):
    agent_select_status_message: str = (
        "Load a URL Data Tab, and we'll access it and use it to generate a response."
    )
    llm_provider: str = "openai_llm"
    llm_model: str = "gpt-4"
    database_provider: str = "local_filestore_database"


class WebAgent(AgentBase):
    AGENT_NAME: str = "web_agent"
    AGENT_UI_NAME: str = "URL Agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "web_prompt.yaml"

    app: Optional[Any] = None
    index: Optional[Any] = None

    def __init__(self, parent_class=None):
        super().__init__(parent_class=parent_class)
        self.config = AppBase.load_service_config(
            class_instance=self, config_class=AgentConfig
        )
        self.ingest_agent = IngestAgent(parent_class)

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
            prompt_template_path = self.DEFAULT_PROMPT_TEMPLATE_PATH

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
            prompt_template_path = self.DEFAULT_PROMPT_TEMPLATE_PATH

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
