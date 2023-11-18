from typing import Annotated, Any, Generator, Literal, Optional, Type, get_args

import gradio as gr
from agents.agent_base import AgentBase
from pydantic import BaseModel, Field
from services.gradio_interface.gradio_base import GradioBase
from services.llm.llm_service import LLMService


class ClassConfigModel(BaseModel):
    llm_provider_name: str = "openai_llm"
    token_utilization: Annotated[float, Field(ge=0, le=1.0)] = 0.5

    class Config:
        extra = "ignore"


class VanillaLLM(AgentBase):
    class_name = Literal["vanillallm_agent"]
    CLASS_NAME: str = get_args(class_name)[0]
    CLASS_UI_NAME = "VanillaLLM Agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "agents/vanillallm/vanillallm_prompt_templates.yaml"
    REQUIRED_CLASSES: list[Type] = [LLMService]

    class_config_model = ClassConfigModel
    config: ClassConfigModel

    list_of_required_class_instances: list[LLMService] = []

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def create_chat(
        self,
        chat_in: str,
        token_utilization: Optional[float] = None,
        stream: Optional[bool] = None,
    ):
        if token_utilization is None:
            token_utilization = self.config.token_utilization

        prompt = self.create_prompt(
            user_input=chat_in,
            llm_provider_name=self.llm_service.llm_provider.CLASS_NAME,  # type: ignore
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
        )

        for response in self.llm_service.create_chat(
            prompt=prompt,
            token_utilization=token_utilization
            if token_utilization is not None
            else self.config.token_utilization,
            stream=stream,
        ):
            yield response["response_content_string"]

    def create_main_chat_ui(self):
        components = {}
        components["token_utilization"] = gr.Slider(
            value=self.config.token_utilization,
            label="Percent of Model Context Size to Use",
            minimum=0.0,
            maximum=1.0,
            step=0.05,
            min_width=0,
        )
        GradioBase.create_settings_event_listener(self.config, components)
        with gr.Tab(label=self.llm_service.CLASS_UI_NAME):
            self.llm_service.create_settings_ui()
