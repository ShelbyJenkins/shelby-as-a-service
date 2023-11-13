from typing import Literal

from services.embedding.embedding_openai import OpenAIEmbedding

AVAILABLE_PROVIDERS_TYPINGS = Literal[OpenAIEmbedding.class_name]
AVAILABLE_PROVIDERS_NAMES: list[str] = [OpenAIEmbedding.CLASS_NAME]
AVAILABLE_PROVIDERS = [
    OpenAIEmbedding,
]
AVAILABLE_PROVIDERS_UI_NAMES = [
    OpenAIEmbedding.CLASS_UI_NAME,
]
