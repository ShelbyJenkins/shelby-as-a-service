from typing import Literal

from services.llm.llm_openai import OpenAILLM

AVAILABLE_PROVIDERS_TYPINGS = Literal[OpenAILLM.class_name]
AVAILABLE_PROVIDERS_NAMES: list[str] = [OpenAILLM.CLASS_NAME]
AVAILABLE_PROVIDERS = [
    OpenAILLM,
]
AVAILABLE_PROVIDERS_UI_NAMES = [
    OpenAILLM.CLASS_UI_NAME,
]
