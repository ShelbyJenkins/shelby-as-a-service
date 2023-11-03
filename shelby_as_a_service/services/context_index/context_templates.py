import typing
from typing import Any, Dict, Optional, Type, Union

# from modules.index.data_model import DataModels
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.database import LocalFileDatabase, PineconeDatabase
from services.document_loading.document_loading_providers import (
    GenericRecursiveWebScraper,
    GenericWebScraper,
)
from services.document_loading.document_loading_service import DocLoadingService


class ContextTemplates:
    class DefaultContextTemplate:
        TEMPLATE_NAME: str = "default_template_name"
        doc_loader_provider_name = GenericRecursiveWebScraper.CLASS_NAME
        doc_loader_config = GenericRecursiveWebScraper.ClassConfigModel(max_depth=3)
        doc_db_provider_name = PineconeDatabase.CLASS_NAME
        text_processing_provider = "test"
        batch_update_enabled = True

    class DefaultContextTemplate1:
        TEMPLATE_NAME: str = "default_template_name"
        doc_loader_provider_name = GenericRecursiveWebScraper.CLASS_NAME
        doc_loader_config = GenericRecursiveWebScraper.ClassConfigModel(max_depth=3)
        doc_db_provider_name = PineconeDatabase.CLASS_NAME
        text_processing_provider = "test"
        batch_update_enabled = True

    AVAILABLE_TEMPLATES: list[
        Union[Type[DefaultContextTemplate], Type[DefaultContextTemplate1]]
    ] = [DefaultContextTemplate, DefaultContextTemplate1]
