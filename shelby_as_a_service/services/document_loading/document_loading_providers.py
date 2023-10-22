import json
import os
import traceback
from typing import Any, Iterator, List, Optional, Type

import gradio as gr
import services.text_processing.text as TextProcess
from app.module_base import ModuleBase
from bs4 import BeautifulSoup
from langchain.document_loaders import GitbookLoader, RecursiveUrlLoader, SitemapLoader, WebBaseLoader
from langchain.schema import Document
from pydantic import BaseModel


class GenericWebScraper(ModuleBase):
    CLASS_NAME: str = "generic_web_scraper"
    CLASS_UI_NAME: str = "Generic Web Scraper"

    class ClassConfigModel(BaseModel):
        agent_select_status_message: str = "Search index to find docs related to request."
        continue_on_failue: bool = True

    config: ClassConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

    def _load(self, url) -> Iterator[Document]:
        documents = WebBaseLoader(web_path=url).load()
        for document in documents:
            document.page_content = TextProcess.clean_text_content(document.page_content)

        return (Document(page_content=doc.page_content, metadata=doc.metadata) for doc in documents)

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            components["continue_on_failue"] = gr.Checkbox(
                value=self.config.continue_on_failue,
                label="Continue On Failure",
                interactive=True,
            )
        # GradioHelper.create_settings_event_listener(self.config, components)

        return components


class GenericRecursiveWebScraper(ModuleBase):
    CLASS_NAME: str = "generic_recursive_web_scraper"
    CLASS_UI_NAME: str = "Generic Resursive Web Scraper"
    REQUIRED_SECRETS: List[str] = []

    class ClassConfigModel(BaseModel):
        exclude_dirs: Optional[str] = None
        max_depth: Optional[int] = 2
        timeout: Optional[int] = 10
        use_async: bool = False
        prevent_outside: bool = True

    config: ClassConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

    @staticmethod
    def custom_extractor(html_text: str) -> str:
        soup = BeautifulSoup(html_text, "html.parser")
        text_element = soup.find(id="content")
        if text_element:
            return text_element.get_text()
        return ""

    def _load(self, url) -> Iterator[Document]:
        documents = RecursiveUrlLoader(url=url, extractor=self.custom_extractor).load()

        return (Document(page_content=doc.page_content, metadata=doc.metadata) for doc in documents)

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            components["exclude_dirs"] = gr.Textbox(
                value=self.config.exclude_dirs,
                label="Exclude dirs.",
                info="A list of subdirectories to exclude.",
                interactive=True,
            )
            components["max_depth"] = gr.Number(
                value=self.config.max_depth,
                label="Max Depth",
                info="The max depth of the recursive loading.",
                interactive=True,
            )
            components["timeout"] = gr.Number(
                value=self.config.timeout,
                label="Timeout Time",
                info="The timeout for the requests, in the unit of seconds.",
                interactive=True,
            )
            components["use_async"] = gr.Checkbox(
                value=self.config.use_async,
                label="Use Async",
                info="Whether to use asynchronous loading, if use_async is true, this function will not be lazy, but it will still work in the expected way, just not lazy.",
                interactive=True,
            )
            components["prevent_outside"] = gr.Checkbox(
                value=self.config.prevent_outside,
                label="Prevent Outside",
                info="IDK",
                interactive=True,
            )
            # GradioHelper.create_settings_event_listener(self.config, components)

        return components

    # class OpenAPILoader(ServiceBase):
    #     def __init__(self, data_source_config: DataSourceConfig):
    #         self.index_agent = data_source_config.index_agent
    #         self.config = data_source_config
    #         self.data_source_config = data_source_config

    #     def load(self):
    #         open_api_specs = self.load_spec()

    #         return open_api_specs

    #     def load_spec(self):
    #         """Load YAML or JSON files."""
    #         open_api_specs = []
    #         file_extension = None
    #         for filename in os.listdir(self.data_source_config.target_url):
    #             if file_extension is None:
    #                 if filename.endswith(".yaml"):
    #                     file_extension = ".yaml"
    #                 elif filename.endswith(".json"):
    #                     file_extension = ".json"
    #                 else:
    #                     # self.data_source_config.index_agent.log_agent.info(f"Unsupported file format: {filename}")
    #                     continue
    #             elif not filename.endswith(file_extension):
    #                 # self.data_source_config.index_agent.log_agent.info(f"Inconsistent file formats in directory: {filename}")
    #                 continue
    #             file_path = os.path.join(self.data_source_config.target_url, filename)
    #             with open(file_path, "r") as file:
    #                 if file_extension == ".yaml":
    #                     open_api_specs.append(yaml.safe_load(file))
    #                 elif file_extension == ".json":
    #                     open_api_specs.append(json.load(file))

    #         return open_api_specs

    # class LoadTextFromFile(ServiceBase):
    #     def __init__(self, data_source_config):
    #         self.config = data_source_config
    #         self.data_source_config = data_source_config

    #     def load(self):
    #         text_documents = self.load_texts()
    #         return text_documents

    # def load_texts(self):
    #     """Load text files and structure them in the desired format."""
    #     text_documents = []
    #     file_extension = ".txt"
    #     for filename in os.listdir(self.data_source_config.target_url):
    #         if not filename.endswith(file_extension):
    #             # Uncomment the line below if you wish to log unsupported file formats
    #             # self.data_source_config.index_agent.log_agent.info(f"Unsupported file format: {filename}")
    #             continue

    #         file_path = os.path.join(self.data_source_config.target_url, filename)
    #         title = os.path.splitext(filename)[0]
    #         with open(file_path, "r", encoding="utf-8") as file:
    #             document_metadata = {
    #                 "loc": file_path,
    #                 "source": file_path,
    #                 "title": title
    #             }
    #             document = Document(page_content=file.read(), metadata=document_metadata)
    #             text_documents.append(document)

    #     return text_documents

    def load_texts(self):
        """Load text and JSON files and structure them in the desired format."""
        text_documents = []
        allowed_extensions = [".txt", ".json"]

        for filename in os.listdir(self.data_source_config.target_url):
            file_extension = os.path.splitext(filename)[1]

            if file_extension not in allowed_extensions:
                # Uncomment the line below if you wish to log unsupported file formats
                # self.data_source_config.index_agent.log_agent.info(f"Unsupported file format: {filename}")
                continue

            file_path = os.path.join(self.data_source_config.target_url, filename)
            title = os.path.splitext(filename)[0]

            with open(file_path, "r", encoding="utf-8") as file:
                if file_extension == ".txt":
                    content = file.read()
                    # You might want to adapt the following based on how you wish to represent JSON content
                    document_metadata = {
                        "loc": file_path,
                        "source": file_path,
                        "title": title,
                    }
                    document = Document(page_content=content, metadata=document_metadata)
                elif file_extension == ".json":
                    content = json.load(file)  # Now content is a dictionary

                    # You might want to adapt the following based on how you wish to represent JSON content
                    document_metadata = {
                        "loc": file_path,
                        "source": file_path,
                        "title": title,
                    }
                    document = Document(page_content=content["content"], metadata=document_metadata)
                text_documents.append(document)

        return text_documents
