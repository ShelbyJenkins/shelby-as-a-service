from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional, Tuple, Type, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
import openai
import services.prompt_templates.prompt_templates as PromptTemplates
import services.text_processing.text as TextProcess
from app_config.app_base import AppBase
from interfaces.webui.gradio_ui import GradioUI
from pydantic import BaseModel, Field
from typing_extensions import Annotated


class OpenAILLM(AppBase):
    MODULE_NAME: str = "openai_llm"
    MODULE_UI_NAME: str = "OpenAI LLM"
    REQUIRED_SECRETS: List[str] = ["openai_api_key"]

    class OpenAILLMModel(BaseModel):
        MODEL_NAME: str
        TOKENS_MAX: int
        COST_PER_K: float

    AVAILABLE_MODELS: List[OpenAILLMModel] = [
        OpenAILLMModel(MODEL_NAME="gpt-4", TOKENS_MAX=8192, COST_PER_K=0.06),
        OpenAILLMModel(MODEL_NAME="gpt-4-32k", TOKENS_MAX=32768, COST_PER_K=0.06),
        OpenAILLMModel(MODEL_NAME="gpt-3.5-turbo", TOKENS_MAX=4096, COST_PER_K=0.03),
        OpenAILLMModel(MODEL_NAME="gpt-3.5-turbo-16k", TOKENS_MAX=16384, COST_PER_K=0.03),
    ]
    UI_MODEL_NAMES = [
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    class ModuleConfigModel(BaseModel):
        model: str = "gpt-3.5-turbo"
        frequency_penalty: Optional[Union[Annotated[float, Field(ge=-2, le=2)], None]] = 0
        max_tokens: Annotated[int, Field(ge=0, le=65536)] = 16384
        presence_penalty: Optional[Union[Annotated[float, Field(ge=-2, le=2)], None]] = 0
        stream: bool = True
        temperature: Optional[Union[Annotated[float, Field(ge=0, le=2.0)], None]] = 1
        top_p: Optional[Union[Annotated[float, Field(ge=0, le=2.0)], None]] = 1

        class Config:
            extra = "ignore"

    config: ModuleConfigModel

    def __init__(self, config_file_dict={}, **kwargs):
        module_config_file_dict = config_file_dict.get(self.MODULE_NAME, {})
        self.config = self.ModuleConfigModel(**{**kwargs, **module_config_file_dict})
        self.set_secrets(self)

    def create_chat(
        self, query, prompt_template_path=None, documents=None, model=None
    ) -> Union[Generator[List[str], None, None], List[str]]:
        prompt, model, request_token_count = self._prep_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            model=model,
        )

        if self.config.stream:
            yield from self._create_streaming_chat(prompt, request_token_count, model)
        else:
            response = openai.ChatCompletion.create(
                api_key=self.secrets["openai_api_key"],
                messages=prompt,
                model=model.MODEL_NAME,
                frequency_penalty=self.config.frequency_penalty,
                max_tokens=self.config.max_tokens,
                presence_penalty=self.config.presence_penalty,
                stream=False,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
            )

            (
                prompt_response,
                total_prompt_tokens,
                total_completion_tokens,
                token_count,
            ) = self._check_response(response, model)

            if not prompt_response:
                return None

            request_token_string = f"Request token count: {total_prompt_tokens}"
            response_token_string = f"Response token count: {total_completion_tokens}"
            total_token_string = f"Total token count: {token_count}"

            yield [
                prompt_response,
                request_token_string,
                response_token_string,
                total_token_string,
            ]
            return None

    def _check_response(self, response, model):
        # Check if keys exist in dictionary
        parsed_response = response.get("choices", [{}])[0].get("message", {}).get("content")

        total_prompt_tokens = int(response.get("usage").get("prompt_tokens", 0))
        total_completion_tokens = int(response.get("usage").get("completion_tokens", 0))

        if not parsed_response:
            raise ValueError(f"Error in response: {response}")

        token_count = total_prompt_tokens + total_completion_tokens
        self._calculate_cost(token_count, model=model)

        return (
            parsed_response,
            total_prompt_tokens,
            total_completion_tokens,
            token_count,
        )

    def _calculate_cost(self, token_count, model):
        # Convert numbers to Decimal
        COST_PER_K_decimal = Decimal(model.COST_PER_K)
        token_count_decimal = Decimal(token_count)

        # Perform the calculation using Decimal objects
        request_cost = COST_PER_K_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        AppBase.total_cost += request_cost
        AppBase.last_request_cost = request_cost
        print(f"Request cost: ${format(request_cost, 'f')}")
        print(f"Total cost: ${format(AppBase.total_cost, 'f')}")

    def _calculate_cost_streaming(self, total_token_count, model):
        # Convert numbers to Decimal
        COST_PER_K_decimal = Decimal(model.COST_PER_K)
        token_count_decimal = Decimal(total_token_count)

        # Perform the calculation using Decimal objects
        request_cost = COST_PER_K_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        AppBase.total_cost += request_cost
        AppBase.last_request_cost = request_cost
        print(f"Total cost: ${format(AppBase.total_cost, 'f')}")

    def _create_streaming_chat(
        self, prompt, request_token_count, model
    ) -> Generator[List[str], None, None]:
        stream = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            messages=prompt,
            model=model.MODEL_NAME,
            frequency_penalty=self.config.frequency_penalty,
            max_tokens=self.config.max_tokens,
            presence_penalty=self.config.presence_penalty,
            stream=True,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
        )

        chunk = {}
        partial_message = ""
        request_token_string = f"Request token count: {request_token_count}"
        response_token_count = 0
        total_token_count = request_token_count
        for chunk in stream:
            delta_content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if len(delta_content) != 0:
                chunk_token_count = TextProcess.tiktoken_len(delta_content, model.MODEL_NAME)
                response_token_count += chunk_token_count
                response_token_string = f"Response token count: {response_token_count}"
                total_token_count += chunk_token_count
                total_token_string = f"Total token count: {total_token_count}"

                partial_message += delta_content
                yield [
                    partial_message,
                    request_token_string,
                    response_token_string,
                    total_token_string,
                ]
            finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
            if finish_reason:
                self._calculate_cost_streaming(
                    total_token_count=total_token_count,
                    model=model,
                )
                return None

    def _prep_chat(
        self, query, prompt_template_path=None, documents=None, model=None
    ) -> Tuple[List[Dict[str, str]], OpenAILLMModel, int]:
        model = self.get_model(self, requested_model_name=model)

        prompt = PromptTemplates.create_openai_prompt(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
        )

        result = ""
        for entry in prompt:
            role = entry.get("role", "")
            content = entry.get("content", "")
            result += f"{role}: {content}\n"
        request_token_count = TextProcess.tiktoken_len(result, encoding_model=model.MODEL_NAME)

        if prompt is None or model is None or request_token_count is None:
            raise ValueError(
                f"Error with input values - prompt: {prompt}, model: {model}, request_token_count: {request_token_count}"
            )
        return prompt, model, request_token_count

    def create_ui(self):
        components = {}
        with gr.Accordion(label="OpenAI", open=False):
            with gr.Column():
                components["model"] = gr.Dropdown(
                    value=self.config.model,
                    choices=GradioHelper.dropdown_choices(OpenAILLM),
                    label="OpenAI LLM Model",
                    interactive=True,
                )
                components["max_tokens"] = gr.Slider(
                    minimum=0,
                    maximum=16384,
                    value=self.config.max_tokens,
                    step=1,
                    label="Max Tokens",
                    interactive=True,
                )
                components["stream"] = gr.Checkbox(
                    value=self.config.stream,
                    label="Stream Response",
                    interactive=True,
                )
                with gr.Accordion(label="Advanced Settings", open=False):
                    components["frequency_penalty"] = gr.Slider(
                        minimum=-2.0,
                        maximum=2.0,
                        value=self.config.frequency_penalty,
                        step=0.05,
                        label="Frequency Penalty",
                        interactive=True,
                    )
                    components["presence_penalty"] = gr.Slider(
                        minimum=-2.0,
                        maximum=2.0,
                        value=self.config.presence_penalty,
                        step=0.05,
                        label="Presence Penalty",
                        interactive=True,
                    )
                    components["temperature"] = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=self.config.temperature,
                        step=0.05,
                        label="Temperature",
                        interactive=True,
                    )
                    components["top_p"] = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=self.config.top_p,
                        step=0.05,
                        label="Top P",
                        interactive=True,
                    )
            GradioUI.create_settings_event_listener(self, components)
        return components
