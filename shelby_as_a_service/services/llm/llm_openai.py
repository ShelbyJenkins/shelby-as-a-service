import typing
from decimal import Decimal
from typing import Any, Literal, Optional, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelpers
import openai
import services.text_processing.text_utils as text_utils
from pydantic import BaseModel, Field
from services.service_base import ServiceBase
from services.text_processing.prompts.prompt_template_service import PromptTemplates
from typing_extensions import Annotated


class OpenAILLM(ServiceBase):
    class_name = Literal["openai_llm"]
    CLASS_NAME: class_name = typing.get_args(class_name)[0]
    CLASS_UI_NAME: str = "OpenAI LLM"
    REQUIRED_SECRETS: list[str] = ["openai_api_key"]
    MODELS_TYPE: str = "llm_models"

    class ModelConfig(BaseModel):
        MODEL_NAME: str
        TOKENS_MAX: int
        COST_PER_K: float
        TOKENS_PER_MESSAGE: int
        TOKENS_PER_NAME: int
        frequency_penalty: Optional[Union[Annotated[float, Field(ge=-2, le=2)], None]] = 0
        max_tokens: Annotated[int, Field(ge=0, le=16384)] = 4096
        presence_penalty: Optional[Union[Annotated[float, Field(ge=-2, le=2)], None]] = 0
        stream: bool = True
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

    class ClassConfigModel(BaseModel):
        enabled_model_name: str = "gpt-3.5-turbo"
        available_models: dict[str, "OpenAILLM.ModelConfig"]

        class Config:
            extra = "ignore"

    config: ClassConfigModel
    llm_models: list
    current_model_class: ModelConfig

    def __init__(self, config: dict[str, Any] = {}, **kwargs):
        super().__init__(config=config, **kwargs)
        self.set_current_model(self.config.enabled_model_name)

    def create_chat_with_provider(
        self,
        query=None,
        llm_model_name: Optional[str] = None,
        max_tokens=None,
        logit_bias=None,
        stream=None,
    ):
        prompt, llm_model, total_prompt_tokens = self.prep_chat(
            query=query,
            llm_model_name=llm_model_name,
        )

        if max_tokens is None:
            max_tokens = llm_model.max_tokens
        while max_tokens + total_prompt_tokens > (llm_model.TOKENS_MAX - 15):
            max_tokens -= 1

        if (llm_model.stream and stream is None) or (stream is True):
            yield from self._create_streaming_chat(
                prompt, max_tokens, total_prompt_tokens, llm_model
            )
        else:
            if logit_bias is None:
                logit_bias = {}

            response = openai.ChatCompletion.create(
                api_key=self.secrets["openai_api_key"],
                messages=prompt,
                model=llm_model.MODEL_NAME,
                frequency_penalty=llm_model.frequency_penalty,
                max_tokens=max_tokens,
                presence_penalty=llm_model.presence_penalty,
                temperature=llm_model.temperature,
                top_p=llm_model.top_p,
                logit_bias=logit_bias,
            )
            (
                prompt_response,
                total_prompt_tokens,
                total_completion_tokens,
                total_token_count,
            ) = self._check_response(response, llm_model)

            response = {
                "response_content_string": prompt_response,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_token_count": total_token_count,
                "model_name": llm_model.MODEL_NAME,
            }
            yield response
            return response

    def _check_response(self, response, llm_model):
        # Check if keys exist in dictionary
        parsed_response = response.get("choices", [{}])[0].get("message", {}).get("content")

        total_prompt_tokens = int(response.get("usage").get("prompt_tokens", 0))
        total_completion_tokens = int(response.get("usage").get("completion_tokens", 0))

        if not parsed_response:
            raise ValueError(f"Error in response: {response}")

        total_token_count = total_prompt_tokens + total_completion_tokens
        self._calculate_cost(total_token_count, llm_model=llm_model)

        return (
            parsed_response,
            total_prompt_tokens,
            total_completion_tokens,
            total_token_count,
        )

    def _calculate_cost(self, total_token_count, llm_model):
        # Convert numbers to Decimal
        COST_PER_K_decimal = Decimal(llm_model.COST_PER_K)
        token_count_decimal = Decimal(total_token_count)

        # Perform the calculation using Decimal objects
        request_cost = COST_PER_K_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        self.total_cost += request_cost
        self.last_request_cost = request_cost
        print(f"Request cost: ${format(request_cost, 'f')}")
        print(f"Total cost: ${format(self.total_cost, 'f')}")

    def _create_streaming_chat(self, prompt, max_tokens, total_prompt_tokens, llm_model):
        stream = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            messages=prompt,
            model=llm_model.MODEL_NAME,
            frequency_penalty=llm_model.frequency_penalty,
            max_tokens=max_tokens,
            presence_penalty=llm_model.presence_penalty,
            stream=True,
            temperature=llm_model.temperature,
            top_p=llm_model.top_p,
        )

        chunk = {}
        response_content_string = ""
        total_completion_tokens = 0
        total_token_count = total_prompt_tokens
        for chunk in stream:
            if isinstance(chunk, list):
                raise ValueError(
                    f"Chunk: {chunk} Error in response: chunk should not be a list here."
                )
            delta_content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if len(delta_content) != 0:
                chunk_token_count = text_utils.tiktoken_len(delta_content, llm_model.MODEL_NAME)
                total_completion_tokens += chunk_token_count
                total_token_count += chunk_token_count

                response_content_string += delta_content

                response = {
                    "response_content_string": response_content_string,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens,
                    "total_token_count": total_token_count,
                    "model_name": llm_model.MODEL_NAME,
                }
                yield response
            finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
            if finish_reason:
                self._calculate_cost(
                    total_token_count=total_token_count,
                    llm_model=llm_model,
                )
                response = {
                    "response_content_string": response_content_string,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens,
                    "total_token_count": total_token_count,
                    "model_name": llm_model.MODEL_NAME,
                }
                return response

    def create_settings_ui(self):
        model_dropdown = gr.Dropdown(
            value=self.config.enabled_model_name,
            choices=self.llm_models,
            label="OpenAI LLM Model",
            interactive=True,
        )

        models_list = []
        for model_name, model in self.config.available_models.items():
            model_compoments = {}

            if self.config.enabled_model_name == model_name:
                visibility = True
            else:
                visibility = False

            with gr.Group(visible=visibility) as model_settings:
                model_compoments["stream"] = gr.Checkbox(
                    value=model.stream,
                    label="Stream Response",
                    interactive=True,
                )
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
            GradioHelpers.create_settings_event_listener(model, model_compoments)

        model_dropdown.change(
            fn=self.set_current_model,
            inputs=model_dropdown,
            outputs=models_list,
        )

    def set_current_model(self, requested_model):
        output = []
        for model_name, model in self.config.available_models.items():
            ui_name = model_name
            if ui_name == requested_model:
                self.current_model_class = model
                self.config.enabled_model_name = ui_name
                ModuleBase.update_settings_file = True
                output.append(gr.Group(visible=True))
            else:
                output.append(gr.Group(visible=False))
        return output
