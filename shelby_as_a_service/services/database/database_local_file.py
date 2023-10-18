import os
from typing import Any, Dict, List, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
import services.text_processing.text as TextProcess
from app_config.module_base import ModuleBase
from pydantic import BaseModel


class LocalFileStoreDatabase(ModuleBase):
    MODULE_NAME: str = "local_filestore_database"
    MODULE_UI_NAME: str = "Local Files as a Database"

    class ModuleConfigModel(BaseModel):
        max_response_tokens: int = 1

    config: ModuleConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

    def write_documents_to_database(self, documents, data_domain, data_source):
        data_domain_name_file_path = os.path.join(
            self.local_index_dir,
            "outputs",
            data_domain.data_domain_name,
        )
        os.makedirs(data_domain_name_file_path, exist_ok=True)
        for document in documents:
            title = TextProcess.extract_and_clean_title(document, data_source.data_source_url)
            valid_filename = "".join(c if c.isalnum() else "_" for c in title)
            file_path = os.path.join(data_domain_name_file_path, f"{valid_filename}.md")
            page_content = document.page_content
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(page_content)

            # Optionally, log the path to which the document was written
            print(f"Document written to: {file_path}")

    def create_settings_ui(self):
        components = {}
        # with gr.Accordion(label=self.MODULE_UI_NAME, open=True):
        #     with gr.Column():
        #         components["max_response_tokens"] = gr.Number(
        #             value=self.config.max_response_tokens,
        #             label="max_response_tokens",
        #             interactive=True,
        #         )
        #     GradioHelper.create_settings_event_listener(self.config, components)

        return components
