from typing import Literal, Type

from services.context_index.doc_index.doc_index_model import (
    DocDBModel,
    DocEmbeddingModel,
    DocIndexModel,
    DocIndexTemplateModel,
    DocIngestProcessorModel,
    DocLoaderModel,
    DomainModel,
    SourceModel,
)

DOC_INDEX_MODEL_NAMES = Literal[
    DocDBModel.class_name,
    DocIndexModel.class_name,
    DocIndexTemplateModel.class_name,
    DocIngestProcessorModel.class_name,
    DocLoaderModel.class_name,
    DomainModel.class_name,
    SourceModel.class_name,
    DocEmbeddingModel.class_name,
]
DOC_INDEX_MODELS: list[Type] = [
    DocDBModel,
    DocIndexModel,
    DocIndexTemplateModel,
    DocIngestProcessorModel,
    DocLoaderModel,
    DomainModel,
    SourceModel,
    DocEmbeddingModel,
]
