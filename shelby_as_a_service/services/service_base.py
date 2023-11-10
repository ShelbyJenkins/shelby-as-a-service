import logging
import os
from typing import Any, Optional, Type

from app.app_base import AppBase
from pydantic import BaseModel
from services.context_index.doc_index.doc_index_model import (
    DocDBModel,
    DocEmbeddingModel,
    DocIngestProcessorModel,
    DocLoaderModel,
    DomainModel,
    SourceModel,
)


class ServiceBase(AppBase):
    CLASS_NAME: str
    CONTEXT_INDEX_PROVIDER_KEY: str
    CLASS_UI_NAME: str
    AVAILABLE_PROVIDERS: list[Type["ServiceBase"]]
    log: logging.Logger
    ClassConfigModel: Type[BaseModel]
    config: BaseModel
    source: SourceModel
    domain: DomainModel

    def __init__(self, config: dict[str, Any] = {}, **kwargs) -> None:
        self.log = logging.getLogger(self.__class__.__name__)

        if (class_config := config.get(self.CLASS_NAME, {})) == {}:
            class_config = config

        merged_config = {**kwargs, **class_config}
        self.config = self.ClassConfigModel(**merged_config)

        self.set_secrets()

    @staticmethod
    def get_requested_class(
        requested_class: str, available_classes: list[Type["ServiceBase"]]
    ) -> Any:
        for available_class in available_classes:
            if (
                available_class.CLASS_NAME == requested_class
                or available_class.CLASS_UI_NAME == requested_class
            ):
                return available_class
        raise ValueError(f"Requested class {requested_class} not found in {available_classes}")

    @classmethod
    def get_requested_class_instance(
        cls, requested_class_name: str, requested_class_config: dict[str, Any] = {}, **kwargs
    ) -> Any:
        for available_class in cls.AVAILABLE_PROVIDERS:
            if (
                available_class.CLASS_NAME == requested_class_name
                or available_class.CLASS_UI_NAME == requested_class_name
            ):
                return available_class(config=requested_class_config, **kwargs)
        raise ValueError(
            f"Requested class {requested_class_name} not found in {cls.AVAILABLE_PROVIDERS}"
        )

    @classmethod
    def get_instance_from_context_index(
        cls,
        domain_or_source: SourceModel | DomainModel,
        doc_db: Optional[DocDBModel] = None,
    ) -> Any:
        context_index_provider: DocLoaderModel | DocIngestProcessorModel | DocEmbeddingModel | DocDBModel
        provider_key = cls.CONTEXT_INDEX_PROVIDER_KEY
        if doc_db:
            context_index_provider = getattr(doc_db, provider_key)
        else:
            context_index_provider = getattr(domain_or_source, provider_key)
        provider_config = context_index_provider.config
        provider_name = context_index_provider.name

        if isinstance(domain_or_source, DomainModel):
            source = None
            domain = domain_or_source
        elif isinstance(domain_or_source, SourceModel):
            source = domain_or_source
            domain = source.domain_model
        else:
            raise ValueError(
                f"Must provide either SourceModel or DomainModel, not {type(domain_or_source)}"
            )

        for available_class in cls.AVAILABLE_PROVIDERS:
            if available_class.CLASS_NAME == provider_name:
                instance = available_class(config=provider_config)
                setattr(instance, "source", source)
                setattr(instance, "domain", domain)
        raise ValueError(f"Requested class {provider_name} not found in {cls.AVAILABLE_PROVIDERS}")

    @property
    def check_for_source(self):
        if getattr(self, "source") == None:
            raise ValueError(f"Must provide SourceModel for {self.__class__.__name__}.")
