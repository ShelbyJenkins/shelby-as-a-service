from typing import Literal

from services.database.local_file import LocalFileDatabase
from services.database.pinecone import PineconeDatabase
from services.database.sqlite import SqliteDatabase

AVAILABLE_PROVIDERS_NAMES = Literal[
    PineconeDatabase.class_name,
    SqliteDatabase.class_name,
]
AVAILABLE_PROVIDERS = [
    PineconeDatabase,
    SqliteDatabase,
]
AVAILABLE_PROVIDERS_UI_NAMES = [
    PineconeDatabase.CLASS_UI_NAME,
    SqliteDatabase.CLASS_UI_NAME,
]
