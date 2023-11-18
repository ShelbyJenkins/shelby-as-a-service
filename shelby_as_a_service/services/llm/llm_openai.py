import typing
from typing import Any, Literal, Optional, Union

import gradio as gr
import services.text_processing.text_utils as text_utils
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from pydantic import BaseModel, Field
from services.gradio_interface.gradio_base import GradioBase
from services.llm.llm_base import LLMBase
from typing_extensions import Annotated


class ClassConfigModel(BaseModel):
    provider_model_name: str = "gpt-3.5-turbo"
    available_models: dict[str, "OpenAILLM.ModelConfig"]

    class Config:
        extra = "ignore"


class OpenAILLM(LLMBase):
    class_name = Literal["openai_llm"]
    CLASS_NAME: str = typing.get_args(class_name)[0]
    CLASS_UI_NAME: str = "OpenAI LLM"
    REQUIRED_SECRETS: list[str] = ["openai_api_key"]
    MODELS_TYPE: str = "llm_models"
    OPENAI_TIMEOUT_SECONDS: float = 60
    class_config_model = ClassConfigModel

    class ModelConfig(BaseModel):
        MODEL_NAME: str
        TOKENS_MAX: int
        COST_PER_K: float
        TOKENS_PER_MESSAGE: int
        TOKENS_PER_NAME: int
        frequency_penalty: Optional[Union[Annotated[float, Field(ge=-2, le=2)], None]] = 0
        max_tokens: Optional[Annotated[int, Field(ge=0, le=16384)]] = 4096
        presence_penalty: Optional[Union[Annotated[float, Field(ge=-2, le=2)], None]] = 0
        temperature: Optional[Union[Annotated[float, Field(ge=0, le=2.0)], None]] = 1
        top_p: Optional[Union[Annotated[float, Field(ge=0, le=2.0)], None]] = 1

    MODEL_DEFINITIONS: dict[str, Any] = {
        "gpt-4": {
            "MODEL_NAME": "gpt-4",
            "TOKENS_MAX": 8192,
            "COST_PER_K": 0.06,
            "TOKENS_PER_MESSAGE": 3,
            "TOKENS_PER_NAME": 1,
        },
        "gpt-4-32k": {
            "MODEL_NAME": "gpt-4-32k",
            "TOKENS_MAX": 32768,
            "COST_PER_K": 0.06,
            "TOKENS_PER_MESSAGE": 3,
            "TOKENS_PER_NAME": 1,
        },
        "gpt-3.5-turbo": {
            "MODEL_NAME": "gpt-3.5-turbo",
            "TOKENS_MAX": 4096,
            "COST_PER_K": 0.03,
            "TOKENS_PER_MESSAGE": 4,
            "TOKENS_PER_NAME": -1,
        },
        "gpt-3.5-turbo-16k": {
            "MODEL_NAME": "gpt-3.5-turbo-16k",
            "TOKENS_MAX": 16384,
            "COST_PER_K": 0.03,
            "TOKENS_PER_MESSAGE": 3,
            "TOKENS_PER_NAME": 1,
        },
    }

    config: ClassConfigModel
    llm_models: list

    def __init__(
        self,
        provider_model_name: Optional[str] = None,
        frequency_penalty: Optional[float] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        config_file_dict: dict[str, Any] = {},
        **kwargs,
    ):
        if not provider_model_name:
            provider_model_name = kwargs.pop("provider_model_name", None)
        else:
            kwargs.pop("provider_model_name", None)
        if not provider_model_name:
            provider_model_name = ClassConfigModel.model_fields["provider_model_name"].default
        super().__init__(
            provider_model_name=provider_model_name,
            frequency_penalty=frequency_penalty,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            temperature=temperature,
            top_p=top_p,
            config_file_dict=config_file_dict,
            **kwargs,
        )
        if self.current_provider_model_instance:
            self.llm_model_instance = self.current_provider_model_instance
        if not self.llm_model_instance:
            raise ValueError("llm_model_instance not properly set!")

    def generate_text(
        self,
        prompt: list,
        max_tokens: int,
    ):
        llm = OpenAI(
            api_key=self.secrets["openai_api_key"],
            max_retries=self.MAX_RETRIES,
            timeout=self.OPENAI_TIMEOUT_SECONDS,
        )
        response = llm.chat.completions.create(
            messages=prompt,
            model=self.llm_model_instance.MODEL_NAME,
            frequency_penalty=self.llm_model_instance.frequency_penalty,
            max_tokens=max_tokens,
            presence_penalty=self.llm_model_instance.presence_penalty,
            temperature=self.llm_model_instance.temperature,
            top_p=self.llm_model_instance.top_p,
        )
        (
            response_message_content,
            total_response_tokens,
        ) = self._check_response(response)

        return {
            "response_content_string": response_message_content,
            "total_response_tokens": total_response_tokens,
        }

    def make_decision(
        self,
        prompt: list,
        logit_bias: dict[str, int],
        max_tokens: int,
        n: int = 1,
    ) -> tuple[list[str] | str, int]:
        llm = OpenAI(
            api_key=self.secrets["openai_api_key"],
            max_retries=self.MAX_RETRIES,
            timeout=self.OPENAI_TIMEOUT_SECONDS,
        )
        responses = llm.chat.completions.create(
            messages=prompt,
            model=self.llm_model_instance.MODEL_NAME,
            frequency_penalty=self.llm_model_instance.frequency_penalty,
            max_tokens=max_tokens,
            presence_penalty=self.llm_model_instance.presence_penalty,
            temperature=self.llm_model_instance.temperature,
            top_p=self.llm_model_instance.top_p,
            logit_bias=logit_bias,
            n=n,
        )
        (
            responses,
            total_response_tokens,
        ) = self._check_response(responses)

        return (
            responses,
            total_response_tokens,
        )

    def create_chat(
        self,
        prompt: list,
        max_tokens: int,
        stream: bool,
    ):
        if stream:
            yield from self._create_streaming_chat(prompt, max_tokens)
        else:
            # response = await OpenAI(
            #     openai_api_key=self.secrets["openai_api_key"],
            #     model_name=self.llm_model_instance.MODEL_NAME,
            #     streaming=stream,
            #     temperature=self.llm_model_instance.temperature,
            #     max_tokens=max_tokens,
            #     top_p=self.llm_model_instance.top_p,
            #     frequency_penalty=self.llm_model_instance.frequency_penalty,
            #     presence_penalty=self.llm_model_instance.presence_penalty,
            #     n=1,
            #     request_timeout=30,
            #     max_retries=3,
            #     logit_bias=None,
            # ).ainvoke(input=prompt)
            llm = OpenAI(
                api_key=self.secrets["openai_api_key"],
                max_retries=self.MAX_RETRIES,
                timeout=self.OPENAI_TIMEOUT_SECONDS,
            )
            response = llm.chat.completions.create(
                messages=prompt,
                model=self.llm_model_instance.MODEL_NAME,
                frequency_penalty=self.llm_model_instance.frequency_penalty,
                max_tokens=max_tokens,
                presence_penalty=self.llm_model_instance.presence_penalty,
                temperature=self.llm_model_instance.temperature,
                top_p=self.llm_model_instance.top_p,
            )
            (
                response_message_content,
                total_response_tokens,
            ) = self._check_response(response)

            response = {
                "response_content_string": response_message_content,
                "total_response_tokens": total_response_tokens,
            }
            yield response
            return response

    def _create_streaming_chat(self, prompt, max_tokens):
        llm = OpenAI(
            api_key=self.secrets["openai_api_key"],
            max_retries=self.MAX_RETRIES,
            timeout=self.OPENAI_TIMEOUT_SECONDS,
        )
        stream = llm.chat.completions.create(
            messages=prompt,
            model=self.llm_model_instance.MODEL_NAME,
            frequency_penalty=self.llm_model_instance.frequency_penalty,
            max_tokens=max_tokens,
            presence_penalty=self.llm_model_instance.presence_penalty,
            stream=True,
            temperature=self.llm_model_instance.temperature,
            top_p=self.llm_model_instance.top_p,
        )

        chunk: ChatCompletionChunk
        response_content_string = ""
        total_response_tokens = 0
        total_token_count = 0
        for chunk in stream:
            if isinstance(chunk, list):
                raise ValueError(
                    f"Chunk: {chunk} Error in response: chunk should not be a list here."
                )
            if not (delta_content := chunk.choices[0].delta.content):
                continue
            if len(delta_content) != 0:
                chunk_token_count = text_utils.tiktoken_len(
                    delta_content, self.llm_model_instance.MODEL_NAME
                )
                total_response_tokens += chunk_token_count
                total_token_count += chunk_token_count

                response_content_string += delta_content

                response = {
                    "response_content_string": response_content_string,
                    "total_response_tokens": total_response_tokens,
                }
                yield response
            if chunk.choices[0].finish_reason:
                response = {
                    "response_content_string": response_content_string,
                    "total_response_tokens": total_response_tokens,
                }
                return response

    def _check_response(self, response: ChatCompletion) -> tuple[list[str] | str, int]:
        response_content = []
        if not (choices := response.choices):
            raise ValueError(f"Error in response: {response}")
        for choice in choices:
            if not (message := choice.message):
                raise ValueError(f"Error in response: {choice}")
            if not (content := message.content):
                raise ValueError(f"Error in response: {message}")
            response_content.append(content)
        if not (usage := response.usage):
            raise ValueError(f"Error in response: {response}")
        if len(response_content) == 1:
            response_content = response_content[0]
        return (response_content, usage.completion_tokens)
        # total_prompt_tokens = int(response.get("usage").get("prompt_tokens", 0))

    def create_settings_ui(self):
        model_dropdown = gr.Dropdown(
            value=self.config.provider_model_name,
            choices=self.llm_models,
            label="OpenAI LLM Model",
            interactive=True,
        )

        models_list = []
        for model_name, model in self.config.available_models.items():
            model_compoments = {}

            if self.config.provider_model_name == model_name:
                visibility = True
            else:
                visibility = False

            with gr.Group(visible=visibility) as model_settings:
                model_compoments["frequency_penalty"] = gr.Slider(
                    minimum=-2.0,
                    maximum=2.0,
                    value=model.frequency_penalty,
                    step=0.05,
                    label="Frequency Penalty",
                    interactive=True,
                )
                model_compoments["presence_penalty"] = gr.Slider(
                    minimum=-2.0,
                    maximum=2.0,
                    value=model.presence_penalty,
                    step=0.05,
                    label="Presence Penalty",
                    interactive=True,
                )
                model_compoments["temperature"] = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    value=model.temperature,
                    step=0.05,
                    label="Temperature",
                    interactive=True,
                )
                model_compoments["top_p"] = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    value=model.top_p,
                    step=0.05,
                    label="Top P",
                    interactive=True,
                )
                model_compoments["max_tokens"] = gr.Number(
                    value=model.TOKENS_MAX,
                    label="model.TOKENS_MAX",
                    interactive=False,
                    info="Maximum Req+Resp Tokens for Model",
                )

            models_list.append(model_settings)
            GradioBase.create_settings_event_listener(model, model_compoments)

        model_dropdown.change(
            fn=self.set_current_model,
            inputs=model_dropdown,
            outputs=models_list,
        )
