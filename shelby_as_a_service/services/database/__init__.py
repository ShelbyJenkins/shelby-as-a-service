from typing import Literal

from services.database.pinecone import PineconeDatabase

AVAILABLE_PROVIDERS_NAMES = Literal[PineconeDatabase.class_name,]
AVAILABLE_PROVIDERS = [
    PineconeDatabase,
]
AVAILABLE_PROVIDERS_UI_NAMES = [
    PineconeDatabase.CLASS_UI_NAME,
]
