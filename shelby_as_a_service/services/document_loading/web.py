from typing import Any, Literal, Optional, get_args

import gradio as gr
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
    CLASS_NAME: class_name = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Generic Web Scraper"

    class ClassConfigModel(BaseModel):
        continue_on_failure: bool = True

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    ui_components: dict[str, Any]

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        super().__init__(config=config, **kwargs)

    def load_docs_with_provider(self, uri) -> list[Document]:
        return WebBaseLoader(web_path=uri).load()

    @classmethod
    def create_provider_ui_components(cls, config_model: ClassConfigModel, visibility: bool = True):
        ui_components = {}

        ui_components["continue_on_failure"] = gr.Checkbox(
            value=config_model.continue_on_failure,
            label="Continue On Failure",
            interactive=True,
            visible=visibility,
        )

        return ui_components


class GenericRecursiveWebScraper(DocLoadingService):
    class_name = Literal["generic_recursive_web_scraper"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Generic Resursive Web Scraper"

    class ClassConfigModel(BaseModel):
        exclude_dirs: Optional[str] = None
        max_depth: Optional[int] = 2
        timeout: Optional[int] = 10
        use_async: bool = False
        prevent_outside: bool = True

    config: ClassConfigModel

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        super().__init__(config=config, **kwargs)

    @staticmethod
    def custom_extractor(html_text: str) -> str:
        soup = BeautifulSoup(html_text, "html.parser")
        text_element = soup.find(id="content")
        if text_element:
            return text_element.get_text()
        return ""

    def load_docs_with_provider(self, uri) -> list[Document]:
        return RecursiveUrlLoader(url=uri, extractor=self.custom_extractor).load()

    @classmethod
    def create_provider_ui_components(cls, config_model: ClassConfigModel, visibility: bool = True):
        ui_components = {}

        ui_components["exclude_dirs"] = gr.Textbox(
            value=config_model.exclude_dirs,
            label="Exclude dirs.",
            info="A list of subdirectories to exclude.",
            interactive=True,
            visible=visibility,
        )
        ui_components["max_depth"] = gr.Number(
            value=config_model.max_depth,
            label="Max Depth",
            info="The max depth of the recursive loading.",
            interactive=True,
            visible=visibility,
        )
        ui_components["timeout"] = gr.Number(
            value=config_model.timeout,
            label="Timeout Time",
            info="The timeout for the requests, in the unit of seconds.",
            interactive=True,
            visible=visibility,
        )
        ui_components["use_async"] = gr.Checkbox(
            value=config_model.use_async,
            label="Use Async",
            info="Whether to use asynchronous loading, if use_async is true, this function will not be lazy, but it will still work in the expected way, just not lazy.",
            interactive=True,
            visible=visibility,
        )
        ui_components["prevent_outside"] = gr.Checkbox(
            value=config_model.prevent_outside,
            label="Prevent Outside",
            info="IDK",
            interactive=True,
            visible=visibility,
        )

        return ui_components
