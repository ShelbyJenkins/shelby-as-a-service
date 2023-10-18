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
    MODULE_UI_NAME: str = "Retrieval"

    REQUIRED_MODULES: List[Type] = [EmbeddingService, DatabaseService]

    class ModuleConfigModel(BaseModel):
        doc_max_tokens: float = 1400
        docs_max_count: float = 4
        topic_constraint_enabled: bool = False
        keyword_generator_enabled: bool = False
        doc_relevancy_check_enabled: bool = False

    config: ModuleConfigModel
    list_of_module_instances: list[Any]
    list_of_module_ui_names: list[Any]
    embedding_service: EmbeddingService
    database_service: DatabaseService

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_module_instance(module_instance=self, config_file_dict=config_file_dict, **kwargs)

    def get_documents(
        self,
        query: str,
        retrieve_n_docs: Optional[int] = None,
        doc_max_tokens: Optional[float] = None,
        max_total_tokens: Optional[float] = None,
        docs_max_count: Optional[float] = None,
        enabled_data_domains: Optional[list[str]] = None,
        topic_constraint_enabled: Optional[bool] = None,
        keyword_generator_enabled: Optional[bool] = None,
        doc_relevancy_check_enabled: Optional[bool] = None,
    ) -> list[dict]:
        """
        Retrieves documents based on a query.

        Args:
            query (str): The query to retrieve documents for.
            retrieve_n_docs (int, optional): The number of documents to retrieve from the database. Defaults to None.
            docs_max_count (int, optional): The maximum number of documents to return from the. Defaults to None.
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

        docs_max_count = docs_max_count if docs_max_count is not None else self.config.docs_max_count
        retrieve_n_docs = retrieve_n_docs if retrieve_n_docs is not None else 4

        returned_documents_list: list[Any] = []
        counter = 0
        while len(returned_documents_list) < docs_max_count:
            returned_documents_list = self._retrieve_docs(
                search_terms=query_embedding,
                retrieve_n_docs=retrieve_n_docs,
                enabled_data_domains=enabled_data_domains,
            )

            returned_documents_list = parse_retrieved_docs(
                retrieved_documents=returned_documents_list,
                doc_max_tokens=doc_max_tokens if doc_max_tokens is not None else self.config.doc_max_tokens,
                max_total_tokens=max_total_tokens if max_total_tokens is not None else 0,
                docs_max_count=docs_max_count if docs_max_count is not None else self.config.docs_max_count,
            )
            if (
                self.config.doc_relevancy_check_enabled
                if doc_relevancy_check_enabled is None
                else doc_relevancy_check_enabled
            ):
                # parsed_documents = ActionAgent.doc_relevancy_check(query, parsed_documents)
                pass
            if returned_documents_list is None:
                returned_documents_list = []
            counter += 1
            retrieve_n_docs += 1

            if counter > 1:
                break

        if returned_documents_list is None or len(returned_documents_list) < 1:
            raise ValueError("No supporting documents found. Currently we don't support queries without supporting context.")
        return returned_documents_list

    def _retrieve_docs(self, search_terms, retrieve_n_docs, enabled_data_domains) -> list[Any]:
        returned_documents_list = []
        for data_domain_name in enabled_data_domains:
            returned_documents = self.database_service.query_index(
                search_terms=search_terms,
                retrieve_n_docs=retrieve_n_docs,
                data_domain_name=data_domain_name,
            )

            returned_documents_list.extend(returned_documents)
        return returned_documents_list

    def create_settings_ui(self):
        components = {}

        with gr.Row():
            components["topic_constraint_enabled"] = gr.Checkbox(
                value=self.config.topic_constraint_enabled,
                label="Topic Constraint",
                interactive=False,
            )
            components["keyword_generator_enabled"] = gr.Checkbox(
                value=self.config.keyword_generator_enabled,
                label="Keyword Generator",
                interactive=False,
            )
            components["doc_relevancy_check_enabled"] = gr.Checkbox(
                value=self.config.doc_relevancy_check_enabled,
                label="Doc Relevancy Check",
                interactive=False,
            )
        with gr.Row():
            components["doc_max_tokens"] = gr.Number(
                value=self.config.doc_max_tokens,
                label="Maximum Document Length",
                minimum=1,
                maximum=10000,
                step=1,
                min_width=0,
            )
            components["docs_max_count"] = gr.Number(
                value=self.config.docs_max_count,
                label="Attempt to retrieve and use this many documents",
                minimum=1,
                maximum=100,
                step=1,
                min_width=0,
            )

        GradioHelper.create_settings_event_listener(self.config, components)

        return components
