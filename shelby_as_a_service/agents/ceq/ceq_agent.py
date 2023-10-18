import re
from typing import Annotated, Any, Generator, Optional, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
import services.text_processing.text as text
from agents.retrieval.retrieval_agent import RetrievalAgent
from app_config.module_base import ModuleBase
from pydantic import BaseModel, Field
from services.llm.llm_service import LLMService


class CEQAgent(ModuleBase):
    """
    CEQ (Context enhanced querying) is a subset of RAG (Retrieval Augmented Generation).
    CEQAgent generates responses to user queries using by
    1) Calculating the amount of tokens available for context documents for a given query and llm model
    2) Retrieving context documents using the RetrievalAgent
    3) Appending the documents to a users query (Prompt Stuffing) for additional context

    Methods:
        run_chat(self, chat_in, llm_provider=None, llm_model=None, model_token_utilization=None,
                 context_to_response_ratio=None, stream=None, sprite_name="webui_sprite"): Generates a response to user input.
    """

    MODULE_NAME: str = "ceq_agent"
    MODULE_UI_NAME: str = "CEQ"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "agents/ceq/ceq_prompt_templates.yaml"
    DATA_DOMAIN_NONE_FOUND_MESSAGE: str = (
        "Query not related to any supported data domains (aka topics). Supported data domains are:"
    )
    REQUIRED_MODULES: list[Type] = [RetrievalAgent, LLMService]

    class ModuleConfigModel(BaseModel):
        """
        The configuration settings for the CEQ agent module.

        Attributes:
            enabled_data_domains (list[str]): A list of enabled data domains.
            context_to_response_ratio (float): The ratio of context tokens to response tokens to use for generating the response.
        """

        enabled_data_domains: list[str] = ["all"]
        context_to_response_ratio: Annotated[float, Field(ge=0, le=1.0)] = 0.5

        class Config:
            extra = "ignore"

    config: ModuleConfigModel
    llm_service: LLMService
    retrieval_agent: RetrievalAgent
    list_of_module_instances: list

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

    def run_chat(
        self,
        chat_in,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        model_token_utilization: Optional[float] = None,
        context_to_response_ratio: Optional[float] = None,
        stream: Optional[bool] = None,
        sprite_name: Optional[str] = "webui_sprite",
    ) -> Union[Generator[str, None, None], dict[str, str]]:
        """
        Generates a response to user input.
        The default values are for the webui, but can be overridden for other interfaces.

        Args:
            chat_in (str): The user input to generate a response for.
            llm_provider (Optional[str]): The LLM provider to use for generating the response.
            llm_model (Optional[str]): The LLM model to use for generating the response.
            model_token_utilization (Optional[float]): The percentage of available tokens to use for generating the response.
            context_to_response_ratio (Optional[float]): The ratio of context tokens to response tokens to use for generating the response.
            stream (Optional[bool]): Whether to stream the response or not.
            sprite_name (Optional[str]): The name of the sprite to use for displaying the response.

        Yields:
            str: The generated response to the user input.
        """
        available_request_tokens, max_tokens = self.llm_service.get_available_request_tokens(
            query=chat_in,
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
            model_token_utilization=model_token_utilization,
            context_to_response_ratio=context_to_response_ratio
            if context_to_response_ratio is not None
            else self.config.context_to_response_ratio,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

        documents = self.retrieval_agent.get_documents(
            query=chat_in,
            max_total_tokens=available_request_tokens,
            enabled_data_domains=self.config.enabled_data_domains,
        )

        previous_response: Optional[dict] = None
        final_response: Optional[dict] = None
        for current_response in self.llm_service.create_chat(
            query=chat_in,
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
            documents=documents,
            llm_provider=llm_provider,
            llm_model=llm_model,
            max_tokens=max_tokens,
            stream=stream,
        ):
            if previous_response is not None:
                yield previous_response["response_content_string"]
            if current_response is not None:
                previous_response = current_response

        final_response = previous_response

        llm_model_name = final_response.get("model_name", None) or "unknown llm model"  # type: ignore
        response_content_string = final_response.get("response_content_string", None)  # type: ignore

        full_response = self._ceq_append_meta(response_content_string, documents, llm_model_name)

        if sprite_name == "webui_sprite":
            yield self._parse_local_markdown(full_response)
        else:
            return full_response

    def _ceq_append_meta(self, response_content_string: str, documents: list[dict], llm_model_name) -> dict[str, str]:
        # Covering LLM doc notations cases
        # The modified pattern now includes optional opening parentheses or brackets before "Document"
        # and optional closing parentheses or brackets after the number
        pattern = r"[\[\(]?Document\s*\[?(\d+)\]?\)?[\]\)]?"
        formatted_text = re.sub(pattern, r"[\1]", response_content_string, flags=re.IGNORECASE)

        # This finds all instances of [n] in the LLM response
        pattern_num = r"\[\d\]"
        matches = re.findall(pattern_num, formatted_text)

        if not matches:
            # self.log.print_and_log("No supporting docs.")
            answer_obj = {
                "response_content_string": response_content_string,
                "llm": llm_model_name,
                "documents": [],
            }
            return answer_obj

        # Formatted text has all mutations of documents n replaced with [n]

        answer_obj = {
            "response_content_string": formatted_text,
            "llm": llm_model_name,
            "documents": [],
        }

        if matches:
            # Creates a lit of each unique mention of [n] in LLM response
            unique_doc_nums = set([int(match[1:-1]) for match in matches])
            for doc_num in unique_doc_nums:
                # doc_num given to llm has an index starting a 1
                # Subtract 1 to get the correct index in the list
                doc_index = doc_num - 1
                # Access the document from the list using the index
                if 0 <= doc_index < len(documents):
                    document = {
                        "doc_num": documents[doc_index]["doc_num"],
                        "url": documents[doc_index]["url"].replace(" ", "-"),
                        "title": documents[doc_index]["title"],
                    }
                    answer_obj["documents"].append(document)
                else:
                    pass
                    self.log.print_and_log(f"Document{doc_num} not found in the list.")

        # self.log.print_and_log(f"response with metadata: {answer_obj}")

        return answer_obj

    def _parse_local_markdown(self, full_response) -> str:
        # Should move this to text processing module
        markdown_string = ""
        # Start with the answer text
        if response_content_string := full_response.get("response_content_string", None):
            markdown_string += f"{response_content_string}\n\n"
        # Add the sources header if there are any documents
        if documents := full_response.get("documents", None):
            markdown_string += "**Sources:**\n"
            # For each document, add a numbered list item with the title and URL
            for doc in documents:
                markdown_string += f"[{doc['doc_num']}] **{doc['title']}**: <{doc['url']}>\n"
        else:
            markdown_string += "No related documents found.\n"

        return markdown_string

    def create_settings_ui(self):
        components = {}

        with gr.Tab(label=self.retrieval_agent.MODULE_UI_NAME):
            components["enabled_data_domains"] = gr.Dropdown(
                choices=["tatum", "None", "all", "Custom"],
                value="all",
                label="Topics to Search",
                multiselect=True,
                min_width=0,
            )
            components["context_to_response_ratio"] = gr.Slider(
                value=self.config.context_to_response_ratio,
                label="Context to Response Ratio",
                minimum=0.0,
                maximum=1.0,
                step=0.05,
                min_width=0,
                info="Percent of the model's context size to use for context docs.",
            )
            self.retrieval_agent.create_settings_ui()
        with gr.Tab(label=self.llm_service.MODULE_UI_NAME):
            self.llm_service.create_settings_ui()

        GradioHelper.create_settings_event_listener(self.config, components)
