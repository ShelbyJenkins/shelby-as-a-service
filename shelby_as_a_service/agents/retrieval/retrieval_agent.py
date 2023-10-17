from typing import Any, Dict, List, Optional, Type

import gradio as gr
import interfaces.webui.gradio_helpers as GradioHelper
from app_config.module_base import ModuleBase
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.embedding.embedding_service import EmbeddingService
from services.text_processing.parse_retrieval_docs import parse_retrieved_docs


class RetrievalAgent(ModuleBase):
    MODULE_NAME: str = "retrieval_agent"
    MODULE_UI_NAME: str = "Retrieval Settings"

    REQUIRED_MODULES: List[Type] = [EmbeddingService, DatabaseService]

    class ModuleConfigModel(BaseModel):
        database_provider: str = "local_filestore_database"
        retrieve_n_docs: int = 6
        doc_max_token_length: int = 1200
        docs_max_total_tokens: int = 2500
        docs_max_count: int = 4
        topic_constraint_enabled: bool = False
        keyword_generator_enabled: bool = False
        doc_relevancy_check_enabled: bool = False

    config: ModuleConfigModel
    embedding_service: EmbeddingService
    database_service: DatabaseService
    list_of_module_instances: list[Any]
    list_of_module_ui_names: list[Any]

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

    def get_documents(
        self,
        query: str,
        retrieve_n_docs: Optional[int] = None,
        docs_max_count: Optional[int] = None,
        enabled_data_domains: Optional[list[str]] = None,
        topic_constraint_enabled: Optional[bool] = None,
        keyword_generator_enabled: Optional[bool] = None,
        doc_relevancy_check_enabled: Optional[bool] = None,
    ) -> list[dict]:
        """
        Retrieves documents based on a query.

        Args:
            query (str): The query to retrieve documents for.
            retrieve_n_docs (int, optional): The number of documents to retrieve. Defaults to None.
            docs_max_count (int, optional): The maximum number of documents to retrieve. Defaults to None.
            enabled_data_domains (list[str], optional): The data domains to retrieve documents from. Defaults to None.
            topic_constraint_enabled (bool, optional): Whether to enable topic constraints. Defaults to None.
            keyword_generator_enabled (bool, optional): Whether to enable keyword generation. Defaults to None.
            doc_relevancy_check_enabled (bool, optional): Whether to enable document relevancy check. Defaults to None.

        Returns:
            List[Dict[str, Any]]: A list of parsed documents.
        """

        if enabled_data_domains is None:
            enabled_data_domains = ["all"]
        if enabled_data_domains == ["all"]:
            print("get all data domains here")
            # enabled_data_domains

        if self.config.topic_constraint_enabled if topic_constraint_enabled is None else topic_constraint_enabled:
            # get all data domains, and then check if returned value is in them
            pass

        if self.config.keyword_generator_enabled if keyword_generator_enabled is None else keyword_generator_enabled:
            #     query_to_embed = self.action_agent.keyword_generator(query)
            #     self.log.print_and_log(
            #         f"ceq_keyword_generator response: {query_to_embed}"
            #     )
            pass

        query_embedding = self.embedding_service.get_query_embedding(query=query)

        returned_documents_list = []
        for data_domain_name in enabled_data_domains:
            returned_documents = self.database_service.query_index(
                search_terms=query_embedding,
                retrieve_n_docs=self.config.retrieve_n_docs if retrieve_n_docs is None else retrieve_n_docs,
                data_domain_name=data_domain_name,
            )
            returned_documents_list.extend(returned_documents)

        parsed_documents = parse_retrieved_docs(
            retrieved_documents=returned_documents_list,
            doc_max_token_length=self.config.doc_max_token_length,
            docs_max_total_tokens=self.config.docs_max_total_tokens,
            docs_max_count=self.config.docs_max_count if docs_max_count is None else docs_max_count,
        )

        if self.config.doc_relevancy_check_enabled if doc_relevancy_check_enabled is None else doc_relevancy_check_enabled:
            # parsed_documents = ActionAgent.doc_relevancy_check(query, parsed_documents)
            pass

        if parsed_documents is None or len(parsed_documents) < 1:
            raise ValueError("No supporting documents found. Currently we don't support queries without supporting context.")
        return parsed_documents

    def create_settings_ui(self):
        components = {}

        with gr.Column():
            for module_instance in self.list_of_module_instances:
                with gr.Tab(label=module_instance.MODULE_UI_NAME):
                    module_instance.create_settings_ui()

                    GradioHelper.create_settings_event_listener(self.config, components)

        return components
