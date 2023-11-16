import logging
from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
from app.app_base import AppBase, LoggerWrapper
from pydantic import BaseModel
from sqlalchemy.orm import Session


class ServiceBase(AppBase):
    CLASS_NAME: str
    DOC_INDEX_KEY: str
    CLASS_UI_NAME: str
    REQUIRED_CLASSES: list[Type["ServiceBase"]]
    logger_wrapper = LoggerWrapper
    ClassConfigModel: Type[BaseModel]
    ModelConfig: Type[BaseModel]
    MODEL_DEFINITIONS: dict[str, Any]
    config: BaseModel
    source: doc_index_models.SourceModel
    domain: doc_index_models.DomainModel
    list_of_class_names: list[str]
    list_of_class_ui_names: list[str]
    list_of_required_class_instances: list[Type]
    session: Session

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs) -> None:
        self.log = self.logger_wrapper(self.__class__.__name__)

        if session := kwargs.get("session"):
            self.session = session

        class_config = config_file_dict.get(self.CLASS_NAME, {})
        if getattr(self, "ClassConfigModel", None):
            merged_config = {**kwargs, **class_config}

            available_models = None
            if model_definitions := getattr(self, "MODEL_DEFINITIONS", None):
                available_models = self.create_model_instances(
                    model_definitions, merged_config, **kwargs
                )
                merged_config["available_models"] = available_models

            self.config = self.ClassConfigModel(**merged_config)

        self.set_secrets()

        if (required_classes := getattr(self, "REQUIRED_CLASSES", None)) is None:
            return
        self.list_of_class_names = []
        self.list_of_class_ui_names = []
        self.list_of_required_class_instances = []
        for required_class in required_classes:
            if (class_name := getattr(required_class, "CLASS_NAME", None)) is None:
                raise Exception(f"Class name not found for {required_class}")

            new_instance: "ServiceBase" = required_class(class_config, **kwargs)
            setattr(self, class_name, new_instance)

            self.list_of_class_names.append(new_instance.CLASS_NAME)
            self.list_of_class_ui_names.append(new_instance.CLASS_UI_NAME)
            self.list_of_required_class_instances.append(new_instance)

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

    @staticmethod
    def get_requested_class_instance(requested_class: str, available_classes: list[Type]) -> Any:
        for available_class in available_classes:
            if (
                available_class.CLASS_NAME == requested_class
                or available_class.CLASS_UI_NAME == requested_class
            ):
                return available_class
        raise ValueError(f"Requested class {requested_class} not found in {available_classes}")

    @classmethod
    def init_requested_class_instance(
        cls, requested_class_name: str, requested_class_config: dict[str, Any] = {}, **kwargs
    ) -> Any:
        for available_class in cls.REQUIRED_CLASSES:
            if (
                available_class.CLASS_NAME == requested_class_name
                or available_class.CLASS_UI_NAME == requested_class_name
            ):
                return available_class(config=requested_class_config, **kwargs)
        raise ValueError(
            f"Requested class {requested_class_name} not found in {cls.REQUIRED_CLASSES}"
        )

    @classmethod
    def init_provider_instance_from_doc_index(
        cls,
        domain_or_source: Optional[
            doc_index_models.SourceModel | doc_index_models.DomainModel
        ] = None,
        doc_index_db_model: Optional[doc_index_models.DocDBModel] = None,
    ) -> Any:
        context_index_provider: doc_index_models.DocLoaderModel | doc_index_models.DocIngestProcessorModel | doc_index_models.DocEmbeddingModel | doc_index_models.DocDBModel
        provider_key = cls.DOC_INDEX_KEY
        if doc_index_db_model:
            context_index_provider = getattr(doc_index_db_model, provider_key)
        elif domain_or_source:
            context_index_provider = getattr(domain_or_source, provider_key)
        else:
            raise ValueError("Must provide either doc_index_db_model or domain_or_source")
        provider_config = context_index_provider.config
        provider_name = context_index_provider.name

        for available_class in cls.REQUIRED_CLASSES:
            if available_class.CLASS_NAME == provider_name:
                return available_class(config=provider_config)
        raise ValueError(f"Requested class {provider_name} not found in {cls.REQUIRED_CLASSES}")

    def create_model_instances(self, model_definitions, module_config_file_dict={}, **kwargs):
        available_models = {}
        list_of_available_model_names = []
        for model_name, definition in model_definitions.items():
            model_config_file_dict = module_config_file_dict.get(model_name, {})
            new_model_instance = self.ModelConfig(**{**model_config_file_dict, **definition})
            list_of_available_model_names.append(model_name)
            available_models[model_name] = new_model_instance

        if models_type := getattr(self, "MODELS_TYPE", None):
            setattr(self, models_type, list_of_available_model_names)
        return available_models

    @staticmethod
    def get_model_instance(requested_model_name: str, provider: "ServiceBase") -> Any:
        for model_name, model in provider.MODEL_DEFINITIONS.items():
            if model_name == requested_model_name:
                model_instance = provider.ModelConfig(**model)
                return model_instance

        raise ValueError(f"Requested model {requested_model_name} not found.")
