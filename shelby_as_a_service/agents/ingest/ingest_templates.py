from typing import Any, Dict, List, Optional, Type

# from modules.index.data_model import DataModels
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.document_loading.document_loading_providers import (
    GenericRecursiveWebScraper,
    GenericWebScraper,
)
from services.document_loading.document_loading_service import DocLoadingService


class IngestTemplates:
    class GenericIngestTemplate:
        TEMPLATE_NAME: str = "Generic Recusive Web Scraper"
        doc_loader_class = GenericRecursiveWebScraper
        text_processing_provider = "test"

    AVAILABLE_TEMPLATES: list = [GenericIngestTemplate]
