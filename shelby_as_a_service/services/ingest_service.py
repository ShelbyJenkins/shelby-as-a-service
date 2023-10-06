import json
import os
import traceback
from typing import Any, Iterator, List, Type

import modules.text_processing.text as TextProcess
from bs4 import BeautifulSoup
from langchain.document_loaders import (
    GitbookLoader,
    RecursiveUrlLoader,
    SitemapLoader,
    WebBaseLoader,
)
from langchain.schema import Document
from pydantic import BaseModel, Field
from services.providers.provider_base import ProviderBase
from services.service_base import ServiceBase


class GenericRecursiveWebScraper(ProviderBase):
    PROVIDER_NAME: str = "generic_recursive_web_scraper"
    PROVIDER_UI_NAME: str = "generic_recursive_web_scraper"
    REQUIRED_SECRETS: List[str] = []

    class ProviderConfigModel(BaseModel):
        agent_select_status_message: str = (
            "Search index to find docs related to request."
        )

    config: ProviderConfigModel

    def __init__(self):
        super().__init__()

    @staticmethod
    def custom_extractor(html_text: str) -> str:
        soup = BeautifulSoup(html_text, "html.parser")
        text_element = soup.find(id="content")
        if text_element:
            return text_element.get_text()
        return ""

    def _load(self, url) -> Iterator[Document]:
        documents = RecursiveUrlLoader(url=url, extractor=self.custom_extractor).load()

        return (
            Document(page_content=doc.page_content, metadata=doc.metadata)
            for doc in documents
        )


class GenericWebScraper(ProviderBase):
    PROVIDER_NAME: str = "generic_web_scraper"
    PROVIDER_UI_NAME: str = "generic_web_scraper"
    REQUIRED_SECRETS: List[str] = []

    class ProviderConfigModel(BaseModel):
        agent_select_status_message: str = (
            "Search index to find docs related to request."
        )

    config: ProviderConfigModel

    def __init__(self):
        super().__init__()

    def _load(self, url) -> Iterator[Document]:
        documents = WebBaseLoader(web_path=url).load()
        for document in documents:
            document.page_content = TextProcess.clean_text_content(
                document.page_content
            )

        return (
            Document(page_content=doc.page_content, metadata=doc.metadata)
            for doc in documents
        )


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
#                     # self.data_source_config.index_agent.log_agent.print_and_log(f"Unsupported file format: {filename}")
#                     continue
#             elif not filename.endswith(file_extension):
#                 # self.data_source_config.index_agent.log_agent.print_and_log(f"Inconsistent file formats in directory: {filename}")
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

#     # def load_texts(self):
#     #     """Load text files and structure them in the desired format."""
#     #     text_documents = []
#     #     file_extension = ".txt"
#     #     for filename in os.listdir(self.data_source_config.target_url):
#     #         if not filename.endswith(file_extension):
#     #             # Uncomment the line below if you wish to log unsupported file formats
#     #             # self.data_source_config.index_agent.log_agent.print_and_log(f"Unsupported file format: {filename}")
#     #             continue

#     #         file_path = os.path.join(self.data_source_config.target_url, filename)
#     #         title = os.path.splitext(filename)[0]
#     #         with open(file_path, "r", encoding="utf-8") as file:
#     #             document_metadata = {
#     #                 "loc": file_path,
#     #                 "source": file_path,
#     #                 "title": title
#     #             }
#     #             document = Document(page_content=file.read(), metadata=document_metadata)
#     #             text_documents.append(document)

#     #     return text_documents

#     def load_texts(self):
#         """Load text and JSON files and structure them in the desired format."""
#         text_documents = []
#         allowed_extensions = [".txt", ".json"]

#         for filename in os.listdir(self.data_source_config.target_url):
#             file_extension = os.path.splitext(filename)[1]

#             if file_extension not in allowed_extensions:
#                 # Uncomment the line below if you wish to log unsupported file formats
#                 # self.data_source_config.index_agent.log_agent.print_and_log(f"Unsupported file format: {filename}")
#                 continue

#             file_path = os.path.join(self.data_source_config.target_url, filename)
#             title = os.path.splitext(filename)[0]

#             with open(file_path, "r", encoding="utf-8") as file:
#                 if file_extension == ".txt":
#                     content = file.read()
#                     # You might want to adapt the following based on how you wish to represent JSON content
#                     document_metadata = {
#                         "loc": file_path,
#                         "source": file_path,
#                         "title": title,
#                     }
#                     document = Document(
#                         page_content=content, metadata=document_metadata
#                     )
#                 elif file_extension == ".json":
#                     content = json.load(file)  # Now content is a dictionary

#                     # You might want to adapt the following based on how you wish to represent JSON content
#                     document_metadata = {
#                         "loc": file_path,
#                         "source": file_path,
#                         "title": title,
#                     }
#                     document = Document(
#                         page_content=content["content"], metadata=document_metadata
#                     )
#                 text_documents.append(document)

#         return text_documents


class IngestService(ServiceBase):
    SERVICE_NAME: str = "ingest_service"
    SERVICE_UI_NAME: str = "ingest_service"
    PROVIDER_TYPE: str = "ingest_provider"
    DEFAULT_PROVIDER: Type = GenericWebScraper
    AVAILABLE_PROVIDERS: List[Type] = [
        GenericWebScraper,
        GenericRecursiveWebScraper,
        # OpenAPILoader,
        # LoadTextFromFile,
    ]

    class ServiceConfigModel(BaseModel):
        agent_select_status_message: str = (
            "Search index to find docs related to request."
        )

    config: ServiceConfigModel

    def __init__(self):
        super().__init__()

    def load(self, data_source):
        provider = self.get_provider(data_source.data_source_ingest_provider)
        if provider:
            return provider._load(data_source.data_source_url)
        else:
            print("rnr")
