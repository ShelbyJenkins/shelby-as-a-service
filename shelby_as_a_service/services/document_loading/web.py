import json
import os
import traceback
import typing
from enum import Enum
from typing import Any, Final, Iterator, Literal, Optional, Type

import gradio as gr
import services.text_processing.text_utils as text_utils
from app.module_base import ModuleBase
from bs4 import BeautifulSoup
from langchain.document_loaders import (
    GitbookLoader,
    RecursiveUrlLoader,
    SitemapLoader,
    WebBaseLoader,
)
from langchain.schema import Document
from pydantic import BaseModel

from .document_loading_service import DocLoadingService


class GenericWebScraper(DocLoadingService):
    class_name = Literal["generic_web_scraper"]
    CLASS_NAME: class_name = typing.get_args(class_name)[0]
    CLASS_UI_NAME: str = "Generic Web Scraper"

    class ClassConfigModel(BaseModel):
        continue_on_failure: bool = True

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    ui_components: dict[str, Any]

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        self.config = self.ClassConfigModel(**kwargs, **config_file_dict)
        # super().__init__(config_file_dict=config_file_dict, **kwargs)

    def load_docs(self, url) -> Optional[list[Document]]:
        documents = WebBaseLoader(web_path=url).load()
        for document in documents:
            document.page_content = text_utils.clean_text_content(document.page_content)

        return [Document(page_content=doc.page_content, metadata=doc.metadata) for doc in documents]

    def create_provider_ui_components(self, visibility: bool = True):
        ui_components = {}

        ui_components["continue_on_failure"] = gr.Checkbox(
            value=self.config.continue_on_failure,
            label="Continue On Failure",
            interactive=True,
            visible=visibility,
        )

        return ui_components


class GenericRecursiveWebScraper(DocLoadingService):
    class_name = Literal["generic_recursive_web_scraper"]
    CLASS_NAME: class_name = typing.get_args(class_name)[0]
    CLASS_UI_NAME: str = "Generic Resursive Web Scraper"

    class ClassConfigModel(BaseModel):
        exclude_dirs: Optional[str] = None
        max_depth: Optional[int] = 2
        timeout: Optional[int] = 10
        use_async: bool = False
        prevent_outside: bool = True

    config: ClassConfigModel

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        # super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.config = self.ClassConfigModel(**kwargs, **config_file_dict)

    @staticmethod
    def custom_extractor(html_text: str) -> str:
        soup = BeautifulSoup(html_text, "html.parser")
        text_element = soup.find(id="content")
        if text_element:
            return text_element.get_text()
        return ""

    def load_docs(self, url) -> Optional[list[Document]]:
        documents = RecursiveUrlLoader(url=url, extractor=self.custom_extractor).load()
        return [Document(page_content=doc.page_content, metadata=doc.metadata) for doc in documents]

    def create_provider_ui_components(self, visibility: bool = True):
        ui_components = {}

        ui_components["exclude_dirs"] = gr.Textbox(
            value=self.config.exclude_dirs,
            label="Exclude dirs.",
            info="A list of subdirectories to exclude.",
            interactive=True,
            visible=visibility,
        )
        ui_components["max_depth"] = gr.Number(
            value=self.config.max_depth,
            label="Max Depth",
            info="The max depth of the recursive loading.",
            interactive=True,
            visible=visibility,
        )
        ui_components["timeout"] = gr.Number(
            value=self.config.timeout,
            label="Timeout Time",
            info="The timeout for the requests, in the unit of seconds.",
            interactive=True,
            visible=visibility,
        )
        ui_components["use_async"] = gr.Checkbox(
            value=self.config.use_async,
            label="Use Async",
            info="Whether to use asynchronous loading, if use_async is true, this function will not be lazy, but it will still work in the expected way, just not lazy.",
            interactive=True,
            visible=visibility,
        )
        ui_components["prevent_outside"] = gr.Checkbox(
            value=self.config.prevent_outside,
            label="Prevent Outside",
            info="IDK",
            interactive=True,
            visible=visibility,
        )

        return ui_components
