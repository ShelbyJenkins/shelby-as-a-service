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
    class_config_model: Type[BaseModel]
    ModelConfig: Type[BaseModel]
    MODEL_DEFINITIONS: dict[str, Any]
    config: BaseModel
    source: doc_index_models.SourceModel
    domain: doc_index_models.DomainModel
    list_of_class_names: list[str]
    list_of_class_ui_names: list[str]
    current_provider_instance: Optional[Type] = None
    current_provider_model_instance: Optional[Type] = None
    session: Session

    list_of_required_class_instances: Optional[list[Type]] = None
    list_of_provider_instances: list[Type]

    def __init__(
        self,
        config_file_dict: dict[str, Any] = {},
        context_index_config: dict[str, Any] = {},
        provider_name: Optional[str] = None,
        provider_model_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.log = self.logger_wrapper(self.__class__.__name__)
        if session := kwargs.get("session"):
            self.session = session

        config_from_file = config_file_dict.get(self.CLASS_NAME, {})
        if getattr(self, "class_config_model", None):
            if config_file_dict and context_index_config:
                raise ValueError("Must provide either config_file_dict or context_index_config")
            if not config_from_file and not context_index_config:
                self.log.info("No config found. Using default config and kwargs.")

            # We prefer configs here over kwargs so we can hardcode the initial setup
            # And then the following inits are configed from file

            merged_config = {
                k: v
                for d in [kwargs, config_from_file, context_index_config]
                for k, v in d.items()
                if v is not None
            }
            if not provider_model_name:
                provider_model_name = merged_config.get("provider_model_name")

            if model_definitions := getattr(self, "MODEL_DEFINITIONS", None):
                if provider_model_name:
                    self.current_provider_model_instance = self.init_model_instance(
                        requested_model_name=provider_model_name,
                        merged_config=merged_config,
                    )

                available_models = self.create_model_instances(
                    model_definitions=model_definitions, merged_config=merged_config
                )
                merged_config["available_models"] = available_models
            self.config = self.class_config_model(**merged_config)

        self.set_secrets()

        if (required_classes := getattr(self, "REQUIRED_CLASSES", None)) is None:
            return

        self.list_of_class_names = []
        self.list_of_class_ui_names = []
        self.list_of_required_class_instances = []
        for required_class in required_classes:
            if (class_name := getattr(required_class, "CLASS_NAME", None)) is None:
                raise Exception(f"Class name not found for {required_class}")
            if provider_name:
                if class_name == provider_name:
                    new_instance: "ServiceBase" = required_class(
                        provider_model_name=provider_model_name,
                        config_file_dict=config_from_file,
                        context_index_config=context_index_config,
                        **kwargs,
                    )
                    self.current_provider_instance = new_instance
                else:
                    continue
            else:
                new_instance: "ServiceBase" = required_class(
                    config_file_dict=config_from_file, **kwargs
                )

            setattr(self, class_name, new_instance)
            self.list_of_class_names.append(new_instance.CLASS_NAME)
            self.list_of_class_ui_names.append(new_instance.CLASS_UI_NAME)
            self.list_of_required_class_instances.append(new_instance)

    @staticmethod
    def get_requested_class(requested_class: str, available_classes: list["ServiceBase"]) -> Any:
        for available_class in available_classes:
            if (
                available_class.CLASS_NAME == requested_class
                or available_class.CLASS_UI_NAME == requested_class
            ):
                return available_class
        raise ValueError(f"Requested class {requested_class} not found in {available_classes}")

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

    def create_model_instances(
        self, model_definitions: dict[str, Any], merged_config: dict[str, Any]
    ):
        available_models = {}
        list_of_available_model_names = []
        for model_name, model in model_definitions.items():
            model_config_file_dict = merged_config.get(model_name, {})
            new_model_instance = self.ModelConfig(**{**model, **model_config_file_dict})
            list_of_available_model_names.append(model_name)
            available_models[model_name] = new_model_instance

        if models_type := getattr(self, "MODELS_TYPE", None):
            setattr(self, models_type, list_of_available_model_names)
        return available_models

    def init_model_instance(self, requested_model_name: str, merged_config: dict[str, Any]) -> Any:
        for model_name, model in self.MODEL_DEFINITIONS.items():
            if model_name == requested_model_name:
                model_instance = self.ModelConfig(**{**model, **merged_config})
                return model_instance

        raise ValueError(f"Requested model {requested_model_name} not found.")
