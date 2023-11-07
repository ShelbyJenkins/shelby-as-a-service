from typing import Literal

from services.embedding.embedding_openai import OpenAIEmbedding

AVAILABLE_PROVIDERS_NAMES = Literal[OpenAIEmbedding.class_name,]
AVAILABLE_PROVIDERS = [
    OpenAIEmbedding,
]
AVAILABLE_PROVIDERS_UI_NAMES = [
    OpenAIEmbedding.CLASS_UI_NAME,
]
