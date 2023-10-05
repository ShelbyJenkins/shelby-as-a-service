# region

from typing import Any, Dict, Generator, List, Optional, Type, Union

import gradio as gr
import modules.utils.config_manager as ConfigManager
import sprites.web.gradio_helpers as GRHelper
from agents.ceq_agent import CEQAgent
from agents.vanillm_agent import VanillaLLM
from agents.web_agent import WebAgent
from app_base import AppBase
from pydantic import BaseModel
from sprites.sprite_base import SpriteBase
from sprites.web.chat_ui import ChatUI
from sprites.web.gradio_themes import AtYourServiceTheme

# endregion


class SpriteConfig(BaseModel):
    default_local_app_enabled: bool = False
    default_local_app_name: Optional[str] = None
    local_message_start: str = "Running request... relax, chill, and vibe a minute."
    local_message_end: str = "Generated by: gpt-4. Memory not enabled. Has no knowledge of past or current queries. For code see https://github.com/shelby-as-a-service/shelby-as-a-service."


class WebSprite(SpriteBase):
    SPRITE_NAME: str = "web_sprite"
    SPRITE_UI_NAME: str = "web_sprite"
    AVAILABLE_AGENTS: List[Type] = [VanillaLLM, WebAgent, CEQAgent]

    def __init__(self):
        """ """
        super().__init__()
        self.config = AppBase.load_service_config(
            class_instance=self, config_class=SpriteConfig
        )

        self.ui = {}

    def create_interface(self):
        """Creates gradio app."""
        with gr.Blocks(theme=AtYourServiceTheme()) as local_client:
            self.ui["chat_ui"] = ChatUI(self).create_ui()

            # with gr.Tab("Data Chat", elem_id="default-tab"):
            #     with gr.Tab("Context Enhanced Querying", elem_id="default-tab"):
            #         self.web_ui()
            #     with gr.Tab("Add Data", elem_id="default-tab"):
            #         # self.create_index_config()
            #         with gr.Tab("email", elem_id="default-tab"):
            #             pass
            #         with gr.Tab("local", elem_id="default-tab"):
            #             pass
            #         with gr.Tab("web", elem_id="default-tab"):
            #             pass

            # with gr.Tab("Build Bots and Websites", elem_id="default-tab"):
            #     self.web_ui()

            # with gr.Tab("Config", elem_id="default-tab"):
            #     self.web_ui()

            # create_index_ui(self)
            # create_web_settings_ui(self)
            local_client.queue()
            local_client.launch()

    def run_chat(
        self, *comps_state
    ) -> Union[Generator[List[str], None, None], List[str]]:
        ui_state = GRHelper.comp_values_to_dict(self.ui, *comps_state)
        documents = None

        agent = self.get_selected_agent(ui_state["chat_tab_agent_dropdown"])
        if agent is None:
            raise gr.Error("Bad value for chat_tab_agent_dropdown!")
        if agent.AGENT_NAME == "web_agent":
            if content := ui_state["web_data_content"]:
                documents = content
            else:
                raise gr.Error("Bad value for web_data_content!")
        # try:
        if ui_state.get("stream_chat", False):
            yield from agent.create_streaming_chat(
                query=ui_state["input_chat_textbox"],
                user_prompt_template_path=None,
                documents=documents,
                llm_provider=ui_state["chat_llm_provider"],
                llm_model=ui_state["chat_llm_model"],
            )
            return None
        else:
            return agent.create_chat(
                query=ui_state["input_chat_textbox"],
                user_prompt_template_path=None,
                document=documents,
                llm_provider=ui_state["chat_llm_provider"],
                llm_model=ui_state["chat_llm_model"],
            )

        # except Exception as e:
        #     print(f"An error occurred: {str(e)}")
        #     raise gr.Error(f"Error: {e}") from e

    def load_single_website(self, *comps_state) -> List[str]:
        comps_state = GRHelper.comp_values_to_dict(self.ui, *comps_state)

        return WebAgent(self).load_single_website(comps_state)

    def _log(self, message):
        self.log.print_and_log_gradio(message)
        gr.Info(message)

    def run_sprite(self):
        self.create_interface()
