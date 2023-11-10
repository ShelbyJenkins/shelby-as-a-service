import typing
from typing import Any, Optional, Type, Union

from pydantic import BaseModel
from services.database import LocalFileDatabase, PineconeDatabase
from services.document_loading.web import GenericRecursiveWebScraper, GenericWebScraper
from services.embedding.embedding_openai import OpenAIEmbedding

from shelby_as_a_service.services.service_base import ServiceBase
from shelby_as_a_service.services.text_processing.ingest.ingest_ceq import IngestCEQ


class ContextTemplates:
    class DefaultContextTemplate:
        TEMPLATE_NAME: str = "default_template_name"
        doc_ingest_processor_provider_name = IngestCEQ.CLASS_NAME
        doc_ingest_processor_config = IngestCEQ.ClassConfigModel()
        doc_loader_provider_name = GenericRecursiveWebScraper.CLASS_NAME
        doc_loader_config = GenericRecursiveWebScraper.ClassConfigModel(max_depth=3)
        doc_db_provider_name = PineconeDatabase.CLASS_NAME
        doc_embedder_provider_name = OpenAIEmbedding.CLASS_NAME
        doc_embedder_config = OpenAIEmbedding.ClassConfigModel()

        batch_update_enabled = True

    class DefaultContextTemplate1:
        TEMPLATE_NAME: str = "default_template_name1"
        doc_ingest_processor_provider_name = IngestCEQ.CLASS_NAME
        doc_ingest_processor_config = IngestCEQ.ClassConfigModel()
        doc_loader_provider_name = GenericRecursiveWebScraper.CLASS_NAME
        doc_loader_config = GenericRecursiveWebScraper.ClassConfigModel(max_depth=2)
        doc_db_provider_name = PineconeDatabase.CLASS_NAME
        doc_embedder_provider_name = OpenAIEmbedding.CLASS_NAME
        doc_embedder_config = OpenAIEmbedding.ClassConfigModel()
        batch_update_enabled = True

    AVAILABLE_TEMPLATES: list[
        Union[Type[DefaultContextTemplate], Type[DefaultContextTemplate1]]
    ] = [DefaultContextTemplate, DefaultContextTemplate1]
