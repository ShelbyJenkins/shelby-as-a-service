from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from context_index.doc_index.docs.context_docs import IngestDoc
from services.service_base import ServiceBase


class IngestProcessingBase(ABC, ServiceBase):
    DOC_INDEX_KEY: str = "enabled_doc_ingest_processor"

    def preprocess_text_with_provider(self, text: str) -> str:
        raise NotImplementedError

    def create_chunks_with_provider(
        self,
        text: str | dict,
    ) -> Optional[list[str]]:
        raise NotImplementedError

    # @classmethod
    # def create_service_ui_components(
    #     cls,
    #     parent_instance: DomainModel | SourceModel,
    #     groups_rendered: bool = True,
    # ):
    #     provider_configs_dict = {}

    #     for provider in parent_instance.doc_loaders:
    #         name = provider.name
    #         config = provider.config
    #         provider_configs_dict[name] = config

    #     text_processing_provider_name = parent_instance.enabled_doc_ingest_processor.name

    #     provider_select_dd, service_providers_dict = GradioBase.abstract_service_ui_components(
    #         service_name=cls.CLASS_NAME,
    #         enabled_provider_name=text_processing_provider_name,
    #         required_classes=cls.REQUIRED_CLASSES,
    #         provider_configs_dict=provider_configs_dict,
    #         groups_rendered=groups_rendered,
    #     )

    #     return provider_select_dd, service_providers_dict
