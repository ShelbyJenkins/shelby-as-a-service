from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.app_base import AppBase


class SettingsView(AppBase):
    MODULE_NAME: str = "settings_view"
    MODULE_UI_NAME: str = "Settings"
    SETTINGS_UI_COL = 4
    PRIMARY_UI_COL = 6

    service: Type

    def __init__(self, webui_sprite):
        self.webui_sprite = webui_sprite
        self.vanillallm_agent = self.webui_sprite.vanillallm_agent

    def create_primary_ui(self):
        components = {}

        with gr.Column(elem_classes="primary_ui_col"):
            components["chat_tab_out_text"] = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder=f"Welcome to {SettingsView.MODULE_UI_NAME}",
                elem_id="chat_tab_out_text",
                elem_classes="chat_tab_out_text_class",
                scale=7,
            )

    def create_settings_ui(self):
        with gr.Column():
            with gr.Tab("Quick Add"):
                with gr.Row():
                    url_or_file = gr.Radio(
                        value="From Website",
                        choices=["From Website", "From Local File"],
                        interactive=True,
                        show_label=False,
                        min_width=0,
                    )
                    gr.Dropdown(
                        value="Github",
                        choices=["Github", "Save to Topic Domain", "Don't Save"],
                        info="Applies presets that improves performance.",
                        interactive=True,
                        show_label=False,
                        min_width=0,
                    )
                    gr.Button(
                        value="Ingest",
                        variant="primary",
                        elem_classes="chat_tab_button",
                        min_width=0,
                    )

                url = gr.Textbox(
                    placeholder="Paste URL Link",
                    lines=1,
                    show_label=False,
                )
                files_box = gr.File(
                    visible=False,
                    label="Drag and drop file",
                )
                file_path = gr.Textbox(
                    placeholder="or Paste Filepath",
                    lines=1,
                    visible=False,
                    show_label=False,
                )

                with gr.Accordion(open=False, label="Custom Loader"):
                    with gr.Row():
                        gr.Dropdown(
                            value="Github",
                            choices=["Github", "Save to Topic Domain", "Don't Save"],
                            label="Source",
                            interactive=True,
                        )
                        gr.Button(
                            value="Test Loader",
                            variant="primary",
                            elem_classes="chat_tab_button",
                            min_width=0,
                        )

                    # Settings go here
                    gr.Checkbox(label="test")
                with gr.Accordion(open=False, label="Custom Text Processor"):
                    with gr.Row():
                        gr.Dropdown(
                            value="Github",
                            choices=["Github", "Save to Topic Domain", "Don't Save"],
                            label="Source",
                            interactive=True,
                        )
                        gr.Button(
                            value="Test Loader",
                            variant="primary",
                            elem_classes="chat_tab_button",
                            min_width=0,
                        )

                    # Settings go here
                    gr.Checkbox(label="test")
                with gr.Accordion(open=False, label="Contextual Compressors and Minifiers"):
                    with gr.Row():
                        gr.Dropdown(
                            value="Github",
                            choices=["Github", "Save to Topic Domain", "Don't Save"],
                            label="Source",
                            interactive=True,
                        )
                        gr.Button(
                            value="Test Loader",
                            variant="primary",
                            elem_classes="chat_tab_button",
                            min_width=0,
                        )

                    # Settings go here
                    gr.Checkbox(label="test")

                with gr.Accordion(open=False, label="Save files and configs"):
                    gr.Dropdown(
                        allow_custom_value=True,
                        value="Save file to Default Domain",
                        choices=[
                            "Save file to Default Domain",
                            "Save to Topic Domain",
                            "Don't Save",
                        ],
                        show_label=False,
                        interactive=True,
                    )
                    gr.Dropdown(
                        allow_custom_value=True,
                        value="Save Config as New Data Source",
                        choices=[
                            "Save Config as New Data Source",
                            "Save to Topic Domain",
                            "Don't Save",
                        ],
                        show_label=False,
                        interactive=True,
                    )
                self.url_or_files_radio_toggle(url_or_file, url, files_box, file_path)
            with gr.Tab(label="Add Topic"):
                pass
            with gr.Tab(label="Index Management"):
                pass
                # self.create_index_management_tab(agent_instance)
        # agent_instance.doc_loading_service.create_settings_ui()

    def url_or_files_radio_toggle(self, url_or_file, url, files_box, file_path):
        def toggle(value):
            if value == "From Website":
                return [gr.Textbox(visible=True), gr.File(visible=False), gr.Textbox(visible=False)]
            return [gr.Textbox(visible=False), gr.File(visible=True), gr.Textbox(visible=True)]

        url_or_file.change(
            fn=toggle,
            inputs=url_or_file,
            outputs=[url, files_box, file_path],
        )

    def create_index_management_tab(self, agent_instance):
        with gr.Tab(label="Index Databases"):
            agent_instance.database_service.create_settings_ui()
        with gr.Tab("Index test"):
            pass
