import json
import os
import re
import shutil
from typing import Any, Dict, Iterator, Literal, Optional, Type, Union, get_args
from urllib.parse import urlparse

import gradio as gr
from langchain.schema import Document
from pydantic import BaseModel

from . import text_utils
from .dfs_text_splitter import DFSTextSplitter
from .ingest_processing_service import IngestProcessingService


class IngestCEQ(IngestProcessingService):
    class_name = Literal["ceq_ingest_processor"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Context Enhanced Query Ingest Processor"
    available_text_splitters: list[str] = ["dfs_text_splitter"]

    class ClassConfigModel(BaseModel):
        enabled_text_splitter: str = "dfs_text_splitter"
        preprocessor_min_length: int = 150
        text_splitter_goal_length: int = 750
        text_splitter_overlap_percent: int = 15  # In percent

    config: ClassConfigModel
    domain_name: str
    source_name: str

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        # super().__init__(config_file_dict=config_file_dict, **kwargs)
        self.config = self.ClassConfigModel(**kwargs, **config_file_dict)

        self.text_splitter = DFSTextSplitter(
            goal_length=self.config.text_splitter_goal_length,
            overlap_percent=self.config.text_splitter_overlap_percent,
        )

    def process_document(self, content: str) -> Optional[list[str]]:
        if text_utils.tiktoken_len(content) < self.config.preprocessor_min_length:
            self.log.info(
                f"🔴 Skipping doc because content length: {text_utils.tiktoken_len(content)} is shorter than minimum: { self.config.preprocessor_min_length}"
            )
            return None

        text_chunks = self.text_splitter.split_text(content)
        if text_chunks is None:
            self.log.info("🔴 Something went wrong with the text splitter.")
            return None
        # If it's not a list, wrap it inside a list
        if not isinstance(text_chunks, list):
            text_chunks = [text_chunks]

        return text_chunks

    def create_provider_ui_components(self, visibility: bool = True) -> dict[str, Any]:
        ui_components = {}
        ui_components["enabled_text_splitter"] = gr.Dropdown(
            value=self.config.enabled_text_splitter,
            label="Enabled text splitter",
            choices=list(self.available_text_splitters),
            visible=visibility,
        )
        ui_components["preprocessor_min_length"] = gr.Number(
            value=self.config.preprocessor_min_length,
            label="Preprocessor min length",
            visible=visibility,
        )
        ui_components["text_splitter_goal_length"] = gr.Number(
            value=self.config.text_splitter_goal_length,
            label="Text splitter goal length",
            visible=visibility,
        )
        ui_components["text_splitter_overlap_percent"] = gr.Number(
            value=self.config.text_splitter_overlap_percent,
            label="Text splitter overlap percent",
            visible=visibility,
        )
        return ui_components
