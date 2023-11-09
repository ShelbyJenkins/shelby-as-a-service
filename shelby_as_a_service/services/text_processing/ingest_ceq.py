from typing import Any, Dict, Iterator, Literal, Optional, Type, Union, get_args

import gradio as gr
from langchain.schema import Document
from pydantic import BaseModel
from services.context_index.context_documents import IngestDoc

from . import text_utils
from .dfs_text_splitter import DFSTextSplitter
from .ingest_processing_service import IngestProcessingService


class IngestCEQ(IngestProcessingService):
    class_name = Literal["ceq_ingest_processor"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Context Enhanced Query Ingest Processor"
    AVAILABLE_TEXT_SPLITTERS: list[str] = ["dfs_text_splitter"]

    class ClassConfigModel(BaseModel):
        enabled_text_splitter: str = "dfs_text_splitter"
        preprocessor_min_length: int = 150
        text_splitter_goal_length: int = 750
        text_splitter_overlap_percent: int = 15  # In percent

    config: ClassConfigModel

    domain_name: str
    source_name: str

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        super().__init__(config=config, **kwargs)

        self.text_splitter = DFSTextSplitter(
            goal_length=self.config.text_splitter_goal_length,
            overlap_percent=self.config.text_splitter_overlap_percent,
        )

    def preprocess_document(self, doc: IngestDoc) -> IngestDoc:
        if isinstance(doc.precleaned_content, dict):
            raise ValueError("IngestDoc precleaned_content must be a string here.")
        doc.cleaned_content = text_utils.clean_text_content(doc.precleaned_content)
        doc.cleaned_content_token_count = text_utils.tiktoken_len(doc.cleaned_content)
        doc.hashed_cleaned_content = text_utils.hash_content(doc.cleaned_content)

        return doc

    def create_chunks_with_provider(self, text: str) -> Optional[list[str]]:
        if text_utils.tiktoken_len(text) < self.config.preprocessor_min_length:
            self.log.info(
                f"🔴 Skipping doc because text length: {text_utils.tiktoken_len(text)} is shorter than minimum: { self.config.preprocessor_min_length}"
            )
            return None

        text_chunks = self.text_splitter.split_text(text)
        if not text_chunks:
            self.log.info("🔴 Something went wrong with the text splitter.")
            return None

        return text_chunks

    @classmethod
    def create_provider_ui_components(cls, config_model: ClassConfigModel, visibility: bool = True):
        ui_components = {}
        ui_components["enabled_text_splitter"] = gr.Dropdown(
            value=config_model.enabled_text_splitter,
            label="Enabled text splitter",
            choices=list(cls.AVAILABLE_TEXT_SPLITTERS),
            visible=visibility,
        )
        ui_components["preprocessor_min_length"] = gr.Number(
            value=config_model.preprocessor_min_length,
            label="Preprocessor min length",
            visible=visibility,
        )
        ui_components["text_splitter_goal_length"] = gr.Number(
            value=config_model.text_splitter_goal_length,
            label="Text splitter goal length",
            visible=visibility,
        )
        ui_components["text_splitter_overlap_percent"] = gr.Number(
            value=config_model.text_splitter_overlap_percent,
            label="Text splitter overlap percent",
            visible=visibility,
        )
        return ui_components
