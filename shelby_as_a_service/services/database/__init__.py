from typing import Literal

from services.database.local_file import LocalFileDatabase
from services.database.pinecone import PineconeDatabase

AVAILABLE_PROVIDERS_NAMES = Literal[
    PineconeDatabase.class_name,
    LocalFileDatabase.class_name,
]
AVAILABLE_PROVIDERS = [
    PineconeDatabase,
    LocalFileDatabase,
]
AVAILABLE_PROVIDERS_UI_NAMES = [
    PineconeDatabase.CLASS_UI_NAME,
    LocalFileDatabase.CLASS_UI_NAME,
]
