from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
import gradio as gr
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.gradio_interface.gradio_base import GradioBase
from services.service_base import ServiceBase
from services.text_processing.process_retrieval import process_retrieved_docs


class DocRetrieval(ServiceBase):
    CLASS_NAME: str = "doc_retrieval"
    CLASS_UI_NAME: str = "doc_retrieval"

    REQUIRED_CLASSES: list[Type] = [DatabaseService]

    class ClassConfigModel(BaseModel):
        doc_max_tokens: float = 1400
        docs_max_count: float = 4
        topic_constraint_enabled: bool = False
        keyword_generator_enabled: bool = False
        doc_relevancy_check_enabled: bool = False

    config: ClassConfigModel
    list_of_class_names: list
    list_of_class_ui_names: list
    list_of_required_class_instances: list[Any]

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def get_documents(
        self,
        query: str,
        retrieve_n_docs: Optional[int] = None,
        doc_max_tokens: Optional[float] = None,
        max_total_tokens: Optional[float] = None,
        docs_max_count: Optional[float] = None,
        enabled_domains: Optional[list[str]] = None,
        topic_constraint_enabled: Optional[bool] = None,
        keyword_generator_enabled: Optional[bool] = None,
        doc_relevancy_check_enabled: Optional[bool] = None,
    ) -> list[dict]:
        """
        Retrieves documents based on a query.

        Args:
            query (str): The query to retrieve documents for.
            retrieve_n_docs (int, optional): The number of documents to retrieve from the database. Defaults to None.
            docs_max_count (int, optional): The maximum number of documents to return from the doc_db. Defaults to None.
            enabled_domains (list[str], optional): The data domains to retrieve documents from. Defaults to None.
            topic_constraint_enabled (bool, optional): Whether to enable topic constraints. Defaults to None.
            keyword_generator_enabled (bool, optional): Whether to enable keyword generation. Defaults to None.
            doc_relevancy_check_enabled (bool, optional): Whether to enable document relevancy check. Defaults to None.

        Returns:
            list[Dict[str, Any]]: A list of parsed documents.
        """

        if enabled_domains is None:
            enabled_domains = ["all"]
        if enabled_domains == ["all"]:
            print("get all data domains here")
            # enabled_domains

        if (
            self.config.topic_constraint_enabled
            if topic_constraint_enabled is None
            else topic_constraint_enabled
        ):
            # get all data domains, and then check if returned value is in them
            pass

        if (
            self.config.keyword_generator_enabled
            if keyword_generator_enabled is None
            else keyword_generator_enabled
        ):
            #     query_to_embed = self.action_agent.keyword_generator(query)
            #     self.log.info(
            #         f"ceq_keyword_generator response: {query_to_embed}"
            #     )
            pass

        docs_max_count = (
            docs_max_count if docs_max_count is not None else self.config.docs_max_count
        )
        retrieve_n_docs = retrieve_n_docs if retrieve_n_docs is not None else 4

        returned_documents_list = []
        for domain_name in enabled_domains:
            # get database provider from domain here
            # we will have to set sources to use the same doc dbs as their domain
            # or search each sources doc_db for the query
            returned_documents = DatabaseService().query_by_terms(
                search_terms=query,
                retrieve_n_docs=retrieve_n_docs,
                domain_name=domain_name,
            )

            returned_documents_list.extend(returned_documents)

        returned_documents_list = process_retrieved_docs(
            retrieved_documents=returned_documents_list,
            doc_max_tokens=doc_max_tokens
            if doc_max_tokens is not None
            else self.config.doc_max_tokens,
            max_total_tokens=max_total_tokens if max_total_tokens is not None else 0,
            docs_max_count=docs_max_count
            if docs_max_count is not None
            else self.config.docs_max_count,
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

        if returned_documents_list is None or len(returned_documents_list) < 1:
            raise ValueError(
                "No supporting documents found. Currently we don't support queries without supporting context."
            )
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

        GradioBase.create_settings_event_listener(self.config, components)

        return components
