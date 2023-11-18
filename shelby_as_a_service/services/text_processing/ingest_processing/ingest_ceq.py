from typing import Any, Iterator, Literal, Optional, Type, Union, get_args

import gradio as gr
import services.text_processing.text_utils as text_utils
from pydantic import BaseModel
from services.text_processing.dfs_text_splitter import DFSTextSplitter
from services.text_processing.ingest_processing.ingest_processing_base import IngestProcessingBase


class ClassConfigModel(BaseModel):
    enabled_text_splitter: str = "dfs_text_splitter"
    preprocessor_min_length: int = 150
    text_splitter_goal_length: int = 750
    text_splitter_overlap_percent: int = 15  # In percent

    class Config:
        extra = "ignore"


class IngestCEQ(IngestProcessingBase):
    class_name = Literal["ceq_ingest_processor"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME: str = "Context Enhanced Query Ingest Processor"
    AVAILABLE_TEXT_SPLITTERS: list[str] = ["dfs_text_splitter"]

    class_config_model = ClassConfigModel
    config: ClassConfigModel

    domain_name: str
    source_name: str

    def __init__(
        self,
        provider_model_name: Optional[str] = None,
        preprocessor_min_length: Optional[int] = None,
        text_splitter_goal_length: Optional[int] = None,
        text_splitter_overlap_percent: Optional[int] = None,
        context_index_config: dict[str, Any] = {},
        config_file_dict: dict[str, Any] = {},
        **kwargs,
    ):
        if not provider_model_name:
            provider_model_name = context_index_config.get("enabled_text_splitter")

        super().__init__(
            enabled_text_splitter=provider_model_name,
            preprocessor_min_length=preprocessor_min_length,
            text_splitter_goal_length=text_splitter_goal_length,
            text_splitter_overlap_percent=text_splitter_overlap_percent,
            config_file_dict=config_file_dict,
            **kwargs,
        )

        self.text_splitter = DFSTextSplitter(
            goal_length=self.config.text_splitter_goal_length,
            overlap_percent=self.config.text_splitter_overlap_percent,
        )

    def preprocess_text_with_provider(self, text: str) -> str:
        return text_utils.clean_text_content(text)

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
