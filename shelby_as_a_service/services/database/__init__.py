from typing import Literal

from services.database.pinecone import PineconeDatabase

AVAILABLE_PROVIDERS_TYPINGS = Literal[PineconeDatabase.class_name,]
AVAILABLE_PROVIDERS_NAMES: list[str] = [PineconeDatabase.CLASS_NAME]
AVAILABLE_PROVIDERS_UI_NAMES = [
    PineconeDatabase.CLASS_UI_NAME,
]

AVAILABLE_PROVIDERS = [
    PineconeDatabase,
]
