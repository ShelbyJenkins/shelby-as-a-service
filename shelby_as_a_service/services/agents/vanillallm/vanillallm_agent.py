import typing
from typing import Annotated, Any, Generator, Literal, Optional, Type, get_args

import gradio as gr
import services.llm as llm
from pydantic import BaseModel, Field
from services.agents.agent_base import AgentBase
from services.gradio_interface.gradio_base import GradioBase
from services.llm.llm_service import LLMService


class VanillaLLM(AgentBase):
    class_name = Literal["vanillallm_agent"]
    CLASS_NAME: class_name = get_args(class_name)[0]
    CLASS_UI_NAME = "VanillaLLM Agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "agents/vanillallm/vanillallm_prompt_templates.yaml"
    REQUIRED_CLASSES: list[Type] = [LLMService]

    class ClassConfigModel(BaseModel):
        agent_select_status_message: str = "EZPZ"
        model_token_utilization: Annotated[float, Field(ge=0, le=1.0)] = 0.5
        llm_provider_name: str = "openai_llm"

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    llm_service: LLMService
    list_of_required_class_instances: list[LLMService] = []

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(
            config_file_dict=config_file_dict, llm_provider_name="openai_llm", **kwargs
        )

    def create_chat(
        self,
        chat_in: str,
        llm_provider_name: llm.AVAILABLE_PROVIDERS_NAMES,
        llm_model_name: str,
        model_token_utilization: Optional[float] = None,
        stream: Optional[bool] = None,
    ):
        prompt = self.create_prompt(
            query=chat_in,
            llm_provider_name=llm_provider_name,
            prompt_template_path=self.DEFAULT_PROMPT_TEMPLATE_PATH,
        )

        for response in self.llm_service.create_chat(
            prompt=prompt,
            llm_provider_name=llm_provider_name,
            llm_model_name=llm_model_name,
            model_token_utilization=model_token_utilization,
            stream=stream,
        ):
            yield response["response_content_string"]
