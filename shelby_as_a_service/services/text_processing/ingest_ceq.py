import json
import os
import re
import shutil
from typing import Any, Dict, Iterator, Optional, Type, Union
from urllib.parse import urlparse

import gradio as gr
from app.module_base import ModuleBase
from langchain.schema import Document
from pydantic import BaseModel

from . import text_utils
from .dfs_text_splitter import DFSTextSplitter


class IngestCEQ(ModuleBase):
    CLASS_NAME: str = "ceq_ingest_processor"
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
        super().__init__(config_file_dict=config_file_dict, **kwargs)

        self.text_splitter = DFSTextSplitter(
            goal_length=self.config.text_splitter_goal_length,
            overlap_percent=self.config.text_splitter_overlap_percent,
        )

    def process_documents(self, documents: Iterator[Document]) -> Optional[list[str]]:
        processed_document_chunks = []
        processed_text_chunks = []

        for i, doc in enumerate(documents):
            # If no doc title use the url and the resource type
            if not doc.metadata.get("title"):
                parsed_url = urlparse(doc.metadata.get("loc"))
                _, tail = os.path.split(parsed_url.path)
                # Strip anything with "." like ".html"
                root, _ = os.path.splitext(tail)
                doc.metadata["title"] = f"{self.source_name}: {root}"

            # Remove bad chars and extra whitespace chars
            doc.page_content = text_utils.clean_text_content(doc.page_content)
            doc.metadata["title"] = text_utils.clean_text_content(doc.metadata["title"])

            self.log.info(f"Processing: {doc.metadata['title']}")

            if text_utils.tiktoken_len(doc.page_content) < self.config.preprocessor_min_length:
                self.log.info(
                    f"🔴 Skipping doc because content length: {text_utils.tiktoken_len(doc.page_content)} is shorter than minimum: { self.config.preprocessor_min_length}"
                )
                continue

            text_chunks = self.text_splitter.split_text(doc.page_content)
            if text_chunks is None:
                self.log.info("🔴 Something went wrong with the text splitter.")
                continue
            # If it's not a list, wrap it inside a list
            if not isinstance(text_chunks, list):
                text_chunks = [text_chunks]

            token_counts = [text_utils.tiktoken_len(chunk) for chunk in text_chunks]
            self.log.info(
                f"🟢 Doc split into {len(text_chunks)} of averge length {int(sum(token_counts) / len(text_chunks))}"
            )

            for text_chunk in text_chunks:
                document_chunk, text_chunk = self.append_metadata(text_chunk, doc)
                processed_document_chunks.append(document_chunk)
                processed_text_chunks.append(text_chunk.lower())

        self.log.info(f"Total docs: {len(documents)}")
        self.log.info(f"Total chunks: {len(processed_document_chunks)}")
        if not processed_document_chunks:
            return None
        token_counts = [text_utils.tiktoken_len(chunk) for chunk in processed_text_chunks]
        self.log.info(f"Min: {min(token_counts)}")
        self.log.info(f"Avg: {int(sum(token_counts) / len(token_counts))}")
        self.log.info(f"Max: {max(token_counts)}")
        self.log.info(f"Total tokens: {int(sum(token_counts))}")

        return processed_document_chunks

    def append_metadata(self, text_chunk, page):
        # Document chunks are the metadata uploaded to vectorstore
        document_chunk = {
            "content": text_chunk,
            "url": page.metadata["source"].strip(),
            "title": page.metadata["title"],
            "data_domain_name": self.domain_name,
            "data_source_name": self.source_name,
        }
        # Text chunks here are used to create embeddings
        text_chunk = f"{text_chunk} title: {page.metadata['title']}"

        return document_chunk, text_chunk

    def compare_chunks(self, data_source, document_chunks):
        folder_path = f"{self.local_index_dir}/outputs/{data_source.data_domain_name}/{data_source.data_source_name}"
        # Create the directory if it does not exist
        os.makedirs(folder_path, exist_ok=True)
        existing_files = os.listdir(folder_path)
        has_changes = False
        # This will keep track of the counts for each title
        title_counter = {}
        # This will hold the titles of new or different chunks
        new_or_changed_chunks = []
        for document_chunk in document_chunks:
            sanitized_title = re.sub(r"\W+", "_", document_chunk["title"])
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # Skip overly long chunks
            # if (
            #     text_utils.tiktoken_len(text_chunk)
            #     > self.config.index_text_splitter_max_length
            # ):
            #     continue
            # Check if we've seen this title before, if not initialize to 0
            if sanitized_title not in title_counter:
                title_counter[sanitized_title] = 0
            file_name = f"{sanitized_title}_{title_counter[sanitized_title]}.json"
            # Increment the counter for this title
            title_counter[sanitized_title] += 1
            if file_name not in existing_files:
                has_changes = True
                new_or_changed_chunks.append(document_chunk["title"])
            else:
                existing_file_path = os.path.join(folder_path, file_name)
                with open(existing_file_path, "r") as f:
                    existing_data = json.load(f)
                    if existing_data != document_chunk:
                        has_changes = True
                        new_or_changed_chunks.append(document_chunk["title"])

        return has_changes, new_or_changed_chunks

    def create_text_chunks(self, data_source, document_chunks):
        checked_document_chunks = []
        checked_text_chunks = []
        # This will keep track of the counts for each title
        title_counter = {}
        for document_chunk in document_chunks:
            sanitized_title = re.sub(r"\W+", "_", document_chunk["title"])
            # Check if we've seen this title before, if not initialize to 0
            if sanitized_title not in title_counter:
                title_counter[sanitized_title] = 0
            # Increment the counter for this title
            title_counter[sanitized_title] += 1
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # Skip overly long chunks
            # if (
            #     text_utils.tiktoken_len(text_chunk)
            #     > self.config.index_text_splitter_max_length
            # ):
            #     continue
            checked_document_chunks.append(document_chunk)
            checked_text_chunks.append(text_chunk.lower())

        return checked_text_chunks, checked_document_chunks

    def write_chunks(self, data_source, document_chunks):
        folder_path = f"{self.local_index_dir}/outputs/{data_source.data_domain_name}/{data_source.data_source_name}"
        # Clear the folder first
        shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
        # This will keep track of the counts for each title
        title_counter = {}
        for document_chunk in document_chunks:
            sanitized_title = re.sub(r"\W+", "_", document_chunk["title"])
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # Skip overly long chunks
            # if (
            #     text_utils.tiktoken_len(text_chunk)
            #     > self.config.index_text_splitter_max_length
            # ):
            #     continue
            # Check if we've seen this title before, if not initialize to 0
            if sanitized_title not in title_counter:
                title_counter[sanitized_title] = 0
            file_name = f"{sanitized_title}_{title_counter[sanitized_title]}.json"
            # Increment the counter for this title
            title_counter[sanitized_title] += 1
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(document_chunk, f, indent=4)

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
