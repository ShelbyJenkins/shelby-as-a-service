from typing import Any, Optional, Type

import context_index.doc_index as doc_index_models
import gradio as gr
import services.text_processing.prompts.prompt_template_service as prompts
from agents.action.action_agent import ActionAgent
from context_index.doc_index.docs.context_docs import RetrievalDoc
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.gradio_interface.gradio_base import GradioBase
from services.service_base import ServiceBase
from services.text_processing.process_retrieval import (
    preprocess_retrieved_docs,
    process_retrieved_docs,
)


class ClassConfigModel(BaseModel):
    doc_max_tokens: int = 1400
    docs_max_count: int = 4
    max_total_tokens: int = 1000
    topic_constraint_enabled: bool = False
    keyword_generator_enabled: bool = False
    doc_relevancy_check_enabled: bool = False
    doc_relevancy_check_consensus_after_n_tries: int = 3
    doc_relevancy_check_llm_provider_name: str = "openai_llm"
    doc_relevancy_check_llm_model_name: str = "gpt-3.5-turbo"


class DocRetrieval(ServiceBase):
    CLASS_NAME: str = "doc_retrieval"
    CLASS_UI_NAME: str = "doc_retrieval"

    DOC_RELEVANCY_CHECK_PROMPTY_TEMPLATE_PATH: str = "agents/ceq/ceq_doc_check.yaml"
    class_config_model = ClassConfigModel
    config: ClassConfigModel
    list_of_class_names: list
    list_of_class_ui_names: list

    def __init__(self, config_file_dict: dict[str, Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)

    def get_documents(
        self,
        query: str,
        retrieve_n_docs: Optional[int] = None,
        doc_max_tokens: Optional[int] = None,
        max_total_tokens: Optional[int] = None,
        docs_max_count: Optional[int] = None,
        enabled_domains: Optional[list[str] | str] = None,
        topic_constraint_enabled: Optional[bool] = None,
        keyword_generator_enabled: Optional[bool] = None,
        doc_relevancy_check_enabled: Optional[bool] = None,
        doc_relevancy_check_consensus_after_n_tries: Optional[int] = None,
        doc_relevancy_check_llm_provider_name: Optional[str] = None,
        doc_relevancy_check_llm_model_name: Optional[str] = None,
    ) -> list[RetrievalDoc]:
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
            enabled_domains = [domain.name for domain in self.doc_index.index.domains]
        if not isinstance(enabled_domains, list):
            enabled_domains = [enabled_domains]
        domain_models = (
            self.doc_index.session.query(doc_index_models.DomainModel)
            .filter(doc_index_models.DomainModel.name.in_(enabled_domains))
            .all()
        )

        docs_max_count = (
            docs_max_count if docs_max_count is not None else self.config.docs_max_count
        )
        doc_max_tokens = (
            doc_max_tokens if doc_max_tokens is not None else self.config.doc_max_tokens
        )
        max_total_tokens = (
            max_total_tokens if max_total_tokens is not None else self.config.max_total_tokens
        )
        if not doc_relevancy_check_enabled:
            doc_relevancy_check_enabled = self.config.doc_relevancy_check_enabled

        if not retrieve_n_docs:
            retrieve_n_docs = docs_max_count + 4

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

        returned_documents_list: list[RetrievalDoc] = []
        for domain in domain_models:
            domain_doc_db_providers: set[doc_index_models.DocDBModel] = set()
            for source in domain.sources:
                domain_doc_db_providers.add(source.enabled_doc_db)

            for domain_doc_db_provider in domain_doc_db_providers:
                returned_documents = DatabaseService(
                    doc_db_provider_name=domain_doc_db_provider.name,  # type: ignore
                    context_index_config=domain_doc_db_provider.config,
                    doc_db_embedding_provider_name=domain_doc_db_provider.enabled_doc_embedder.name,  # type: ignore
                    doc_db_embedding_provider_config=domain_doc_db_provider.enabled_doc_embedder.config,
                ).query_by_terms(
                    search_terms=query,
                    retrieve_n_docs=retrieve_n_docs,
                    domain_name=domain.name,
                )

                returned_documents_list.extend(returned_documents)
            domain_doc_db_providers.clear()

        preproc_docs = preprocess_retrieved_docs(
            retrieved_documents=returned_documents_list,
            max_total_tokens=max_total_tokens,
            doc_max_tokens=doc_max_tokens,
        )

        if doc_relevancy_check_enabled:
            preproc_docs = self.doc_relevancy_check(
                user_input=query,
                preproc_docs=preproc_docs,
                llm_provider_name=doc_relevancy_check_llm_provider_name,
                llm_model_name=doc_relevancy_check_llm_model_name,
                consensus_after_n_tries=doc_relevancy_check_consensus_after_n_tries,
            )

        processed_docs_list = process_retrieved_docs(
            retrieved_documents=preproc_docs,
            max_total_tokens=max_total_tokens,
            docs_max_count=docs_max_count,
        )

        if processed_docs_list is None:
            processed_docs_list = []

        if processed_docs_list is None or len(processed_docs_list) < 1:
            raise ValueError(
                "No supporting documents found. Currently we don't support queries without supporting context."
            )
        return processed_docs_list

    def doc_relevancy_check(
        self,
        user_input: str,
        preproc_docs: list[RetrievalDoc],
        consensus_after_n_tries: Optional[int] = None,
        llm_provider_name: Optional[str] = None,
        llm_model_name: Optional[str] = None,
        prompt_string: Optional[str] = None,
        prompt_template_path: Optional[str] = None,
    ) -> list[RetrievalDoc]:
        if consensus_after_n_tries is None:
            consensus_after_n_tries = self.config.doc_relevancy_check_consensus_after_n_tries
        if llm_provider_name is None:
            llm_provider_name = self.config.doc_relevancy_check_llm_provider_name
        if llm_model_name is None:
            llm_model_name = self.config.doc_relevancy_check_llm_model_name
        if prompt_string is None and prompt_template_path is None:
            prompt_template_path = self.DOC_RELEVANCY_CHECK_PROMPTY_TEMPLATE_PATH

        action_agent = ActionAgent(
            llm_provider_name=llm_provider_name,  # type: ignore
            llm_model_name=llm_model_name,
        )

        relevant_docs: list[RetrievalDoc] = []
        for doc in preproc_docs:
            if action_agent.boolean_classifier(
                feature=doc.context_chunk,
                user_input=user_input,
                prompt_string=prompt_string,
                prompt_template_path=prompt_template_path,
                consensus_after_n_tries=consensus_after_n_tries,
            ):
                relevant_docs.append(doc)
        return relevant_docs

    def create_settings_ui(self):
        components = {}

        with gr.Row():
            # components["topic_constraint_enabled"] = gr.Checkbox(
            #     value=self.config.topic_constraint_enabled,
            #     label="Topic Constraint",
            #     interactive=False,
            # )
            # components["keyword_generator_enabled"] = gr.Checkbox(
            #     value=self.config.keyword_generator_enabled,
            #     label="Keyword Generator",
            #     interactive=False,
            # )
            components["doc_relevancy_check_enabled"] = gr.Checkbox(
                value=self.config.doc_relevancy_check_enabled,
                label="Doc Relevancy Check",
            )
            components["doc_relevancy_check_consensus_after_n_tries"] = gr.Number(
                value=self.config.doc_relevancy_check_consensus_after_n_tries,
                label="Generate a consensus for each document's relevancy with N Tries",
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
