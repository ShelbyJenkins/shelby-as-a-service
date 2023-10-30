# region

import typing
from typing import Any, Generator, Optional, Type
from urllib.parse import urlparse, urlunparse

import gradio as gr
import services.text_processing.text as text
from agents.ingest.ingest_agent import IngestAgent
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.llm.llm_service import LLMService

# endregion
#


class WebAgent(ModuleBase):
    CLASS_NAME: str = "web_agent"
    CLASS_UI_NAME: str = "URL Agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "web_prompt.yaml"
    REQUIRED_CLASSES: list[Type] = [LLMService, IngestAgent]

    class ClassConfigModel(BaseModel):
        agent_select_status_message: str = (
            "Load a URL Data Tab, and we'll access it and use it to generate a response."
        )
        llm_provider: str = "openai_llm"
        llm_model: str = "gpt-4"
        database_provider: str = "local_file_database"

    config: ClassConfigModel

    def __init__(self):
        pass

    def create_streaming_chat(
        self,
        query,
        user_prompt_template_path=None,
        documents=None,
        llm_provider=None,
        llm_model=None,
    ):
        self.log.info(f"Running query: {query}")

        if user_prompt_template_path:
            prompt_template_path = user_prompt_template_path
        else:
            prompt_template_path = self.DEFAULT_PROMPT_TEMPLATE_PATH

        self.log.info("Sending prompt to LLM")
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
        self.log.info(f"Running query: {query}")

        if user_prompt_template_path:
            prompt_template_path = user_prompt_template_path
        else:
            prompt_template_path = self.DEFAULT_PROMPT_TEMPLATE_PATH

        self.log.info("Sending prompt to LLM")
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
