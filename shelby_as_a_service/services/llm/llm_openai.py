from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Generator, Optional, Union

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
import openai
import services.prompt_templates.prompt_templates as PromptTemplates
import services.text_processing.text as TextProcess
from app_config.module_base import ModuleBase
from pydantic import BaseModel, Field
from typing_extensions import Annotated


class OpenAILLM(ModuleBase):
    MODULE_NAME: str = "openai_llm"
    MODULE_UI_NAME: str = "OpenAI LLM"
    REQUIRED_SECRETS: list[str] = ["openai_api_key"]
    MODELS_TYPE: str = "llm_models"

    class ModelConfig(BaseModel):
        MODEL_NAME: str
        TOKENS_MAX: int
        COST_PER_K: float
        frequency_penalty: Optional[Union[Annotated[float, Field(ge=-2, le=2)], None]] = 0
        max_tokens: Annotated[int, Field(ge=0, le=16384)] = 8192
        presence_penalty: Optional[Union[Annotated[float, Field(ge=-2, le=2)], None]] = 0
        stream: bool = True
        temperature: Optional[Union[Annotated[float, Field(ge=0, le=2.0)], None]] = 1
        top_p: Optional[Union[Annotated[float, Field(ge=0, le=2.0)], None]] = 1

    MODEL_DEFINITIONS: dict[str, Any] = {
        "gpt-4": {"MODEL_NAME": "gpt-4", "TOKENS_MAX": 8192, "COST_PER_K": 0.06},
        "gpt-4-32k": {"MODEL_NAME": "gpt-4-32k", "TOKENS_MAX": 32768, "COST_PER_K": 0.06},
        "gpt-3.5-turbo": {"MODEL_NAME": "gpt-3.5-turbo", "TOKENS_MAX": 4096, "COST_PER_K": 0.03},
        "gpt-3.5-turbo-16k": {"MODEL_NAME": "gpt-3.5-turbo-16k", "TOKENS_MAX": 16384, "COST_PER_K": 0.03},
    }

    class ModuleConfigModel(BaseModel):
        current_model_name: str = "gpt-3.5-turbo"
        available_models: dict[str, "OpenAILLM.ModelConfig"]

        class Config:
            extra = "ignore"

    config: ModuleConfigModel
    llm_models: list
    current_model_class: ModelConfig

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)
        self.set_current_model(self.config.current_model_name)

    def create_chat(
        self,
        query=None,
        prompt_template_path=None,
        documents=None,
        model=None,
        max_tokens=None,
        logit_bias=None,
        stream=None,
    ):
        prompt, model, request_token_count = self._prep_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=documents,
            model=model,
        )
        if max_tokens is None:
            max_tokens = model.max_tokens
        if max_tokens > model.TOKENS_MAX:
            max_tokens = model.TOKENS_MAX - request_token_count - 200
        else:
            max_tokens = max_tokens - request_token_count - 200

        if (model.stream and stream is None) or (stream is True):
            yield from self._create_streaming_chat(prompt, max_tokens, request_token_count, model)
        if stream is None:
            stream = False
        if logit_bias is None:
            logit_bias = {}

        if model.stream is False or stream is False:
            response = openai.ChatCompletion.create(
                api_key=self.secrets["openai_api_key"],
                messages=prompt,
                model=model.MODEL_NAME,
                frequency_penalty=model.frequency_penalty,
                max_tokens=max_tokens,
                presence_penalty=model.presence_penalty,
                temperature=model.temperature,
                top_p=model.top_p,
                logit_bias=logit_bias,
            )
            # (
            #     prompt_response,
            #     total_prompt_tokens,
            #     total_completion_tokens,
            #     token_count,
            # ) = self._check_response(response, model)

            # if not prompt_response:
            #     return None

            # request_token_string = f"Request token count: {total_prompt_tokens}"
            # response_token_string = f"Response token count: {total_completion_tokens}"
            # total_token_string = f"Total token count: {token_count}"

            yield response.get("choices", [{}])[0].get("message", {}).get("content")

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

        self.total_cost += request_cost
        self.last_request_cost = request_cost
        print(f"Request cost: ${format(request_cost, 'f')}")
        print(f"Total cost: ${format(self.total_cost, 'f')}")

    def _calculate_cost_streaming(self, total_token_count, model):
        # Convert numbers to Decimal
        COST_PER_K_decimal = Decimal(model.COST_PER_K)
        token_count_decimal = Decimal(total_token_count)

        # Perform the calculation using Decimal objects
        request_cost = COST_PER_K_decimal * (token_count_decimal / 1000)

        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")

        self.total_cost += request_cost
        self.last_request_cost = request_cost
        print(f"Total cost: ${format(self.total_cost, 'f')}")

    def _create_streaming_chat(self, prompt, max_tokens, request_token_count, model):
        stream = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            messages=prompt,
            model=model.MODEL_NAME,
            frequency_penalty=model.frequency_penalty,
            max_tokens=max_tokens,
            presence_penalty=model.presence_penalty,
            stream=True,
            temperature=model.temperature,
            top_p=model.top_p,
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
                yield partial_message

            finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
            if finish_reason:
                self._calculate_cost_streaming(
                    total_token_count=total_token_count,
                    model=model,
                )

    def _prep_chat(self, query, prompt_template_path=None, documents=None, model=None):
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
            raise ValueError(f"Error with input values - prompt: {prompt}, model: {model}, request_token_count: {request_token_count}")
        return prompt, model, request_token_count

    def create_ui(self):
        components = {}
        with gr.Accordion(label="OpenAI", open=True):
            model_dropdown = gr.Dropdown(
                value=self.config.current_model_name,
                choices=self.llm_models,
                label="OpenAI LLM Model",
                interactive=True,
            )

            models_list = []
            for model_name, model in self.config.available_models.items():
                model_compoments = {}

                if self.config.current_model_name == model_name:
                    visibility = True
                else:
                    visibility = False

                with gr.Group(label=model_name, open=True, visible=visibility) as model_settings:
                    model_compoments["max_tokens"] = gr.Slider(
                        minimum=0,
                        maximum=model.TOKENS_MAX,
                        value=model.max_tokens,
                        step=1,
                        label="Max Tokens",
                        interactive=True,
                    )
                    model_compoments["stream"] = gr.Checkbox(
                        value=model.stream,
                        label="Stream Response",
                        interactive=True,
                    )
                    with gr.Accordion(label="Advanced Settings", open=False):
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

                models_list.append(model_settings)
                GradioHelper.create_settings_event_listener(model, model_compoments)

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
                self.config.current_model_name = ui_name
                ModuleBase.update_settings_file = True
                output.append(gr.Group(label=ui_name, visible=True))
            else:
                output.append(gr.Group(label=ui_name, visible=False))
        return output
