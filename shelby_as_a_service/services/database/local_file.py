import os
import typing
from typing import Any, Dict, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
import services.text_processing.text_utils as text_utils
from app.module_base import ModuleBase
from pydantic import BaseModel


class LocalFileDatabase(ModuleBase):
    CLASS_NAME: str = "local_file_database"
    CLASS_UI_NAME: str = "Local Files as a Database"

    class ClassConfigModel(BaseModel):
        max_response_tokens: int = 1

    config: ClassConfigModel

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def write_documents_to_database(self, documents, data_domain, data_source):
        data_domain_name_file_path = os.path.join(
            self.local_index_dir,
            "outputs",
            data_domain.data_domain_name,
        )
        os.makedirs(data_domain_name_file_path, exist_ok=True)
        for document in documents:
            title = text_utils.extract_and_clean_title(document, data_source.data_source_url)
            valid_filename = "".join(c if c.isalnum() else "_" for c in title)
            file_path = os.path.join(data_domain_name_file_path, f"{valid_filename}.md")
            page_content = document.page_content
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(page_content)

            # Optionally, log the path to which the document was written
            print(f"Document written to: {file_path}")

    def create_settings_ui(self):
        components = {}

        return components

    def create_provider_ui_components(self, visibility: bool = True):
        ui_components = {}

        return ui_components
