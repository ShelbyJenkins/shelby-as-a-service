# region
import json
import re
import traceback
from typing import Any, Dict, List, Optional

import modules.text_processing.text as text
from agents.agent_base import AgentBase
from services.database_service import DatabaseService
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService

# endregion


class CEQAgent(AgentBase):
    agent_name: str = "ceq_agent"
    ui_name: str = "Shelby Agent"
    agent_select_status_message: str = "Search index to find docs related to request."
    default_prompt_template_path: str = "ceq_main_prompt.yaml"

    llm_provider: str = "openai_llm"
    llm_model: str = "gpt-4"
    embedding_provider: str = "openai_embedding"
    data_domain_constraints_enabled: bool = False
    data_domain_none_found_message: str = "Query not related to any supported data domains (aka topics). Supported data domains are:"
    keyword_generator_enabled: bool = False
    doc_relevancy_check_enabled: bool = False
    retrieve_n_docs: int = 5
    docs_max_token_length: int = 1200
    docs_max_total_tokens: int = 2500
    docs_max_used: int = 5

    def __init__(self, parent_sprite=None):
        super().__init__(parent_sprite=parent_sprite)

        self.llm_service = LLMService(self)
        self.embedding_service = EmbeddingService(self)
        self.database_service = DatabaseService(self)
        self.user_prompt_template_path: Optional[str] = None
        self.data_domain_name = None

    def create_streaming_chat(
        self,
        query,
        user_prompt_template_path=None,
        provider_name=None,
        model_name=None,
        **kwargs,
    ):
        prompt_template_path, prepared_documents = self.run_context_enriched_query(
            query, user_prompt_template_path, provider_name, model_name
        )
        yield from self.llm_service.create_streaming_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=prepared_documents,
            provider_name=provider_name,
            model_name=model_name,
        )

    def create_chat(
        self,
        query,
        user_prompt_template_path=None,
        provider_name=None,
        model_name=None,
        **kwargs,
    ):
        prompt_template_path, prepared_documents = self.run_context_enriched_query(
            query, user_prompt_template_path, provider_name, model_name
        )
        llm_response = self.llm_service.create_chat(
            query=query,
            prompt_template_path=prompt_template_path,
            documents=prepared_documents,
            provider_name=provider_name,
            model_name=model_name,
        )
        parsed_response = self.ceq_append_meta(llm_response, prepared_documents)
        self.log.print_and_log(
            f"LLM response with appended metadata: {json.dumps(parsed_response, indent=4)}"
        )

        return parsed_response

    def run_context_enriched_query(
        self, query, user_prompt_template_path=None, provider_name=None, model_name=None
    ):
        if user_prompt_template_path:
            prompt_template_path = user_prompt_template_path
        else:
            prompt_template_path = self.default_prompt_template_path
        query = query

        # try:

        # if self.data_domain_constraints_enabled:
        # self.data_domain_name, response = self.select_data_domain(query)
        #     if response:
        #         return response
        # self.log.print_and_log(f"Running query: {query}")
        query_to_embed = query
        # if self.keyword_generator_enabled:
        #     query_to_embed = self.action_agent.keyword_generator(query)
        #     self.log.print_and_log(
        #         f"ceq_keyword_generator response: {query_to_embed}"
        #     )

        query_embedding = self.embedding_service.get_query_embedding(query_to_embed)

        returned_documents = self.database_service.query_index(
            query_embedding, self.retrieve_n_docs, self.data_domain_name
        )

        prepared_documents = self.doc_handling(returned_documents)

        if not prepared_documents:
            raise ValueError(
                "No supporting documents found. Currently we don't support queries without supporting context."
            )

        self.log.print_and_log("Sending prompt to LLM")
        return prompt_template_path, prepared_documents

    def doc_handling(self, returned_documents):
        if not returned_documents:
            self.log.print_and_log("No supporting documents after initial query!")
            return None

        returned_documents_list = []
        for returned_doc in returned_documents:
            returned_documents_list.append(returned_doc["url"])
        self.log.print_and_log(
            f"{len(returned_documents)} documents returned from vectorstore: {returned_documents_list}"
        )

        if self.doc_relevancy_check_enabled:
            returned_documents = self.doc_relevancy_check(query, returned_documents)
            if not returned_documents:
                self.log.print_and_log(
                    "No supporting documents after doc_relevancy_check!"
                )
                return None
            returned_documents_list = []
            for returned_doc in returned_documents:
                returned_documents_list.append(returned_doc["url"])
            self.log.print_and_log(
                f"{len(returned_documents)} documents returned from doc_check: {returned_documents_list}"
            )

        parsed_documents = self.ceq_parse_documents(returned_documents)
        final_documents_list = []
        for parsed_document in parsed_documents:
            final_documents_list.append(parsed_document["url"])
        self.log.print_and_log(
            f"{len(parsed_documents)} documents returned after parsing: {final_documents_list}"
        )

        if not parsed_documents:
            self.log.print_and_log("No supporting documents after parsing!")
            return None

        return parsed_documents

    def ceq_parse_documents(self, returned_documents=None):
        def _docs_tiktoken_len(documents):
            token_count = 0
            for document in documents:
                tokens = 0
                tokens += text.tiktoken_len(document["content"])

                token_count += tokens
            return token_count

        # Count the number of 'hard' and 'soft' documents
        hard_count = sum(1 for doc in returned_documents if doc["doc_type"] == "hard")
        soft_count = sum(1 for doc in returned_documents if doc["doc_type"] == "soft")

        # Sort the list by score
        sorted_documents = sorted(
            returned_documents, key=lambda x: x["score"], reverse=True
        )

        for i, document in enumerate(sorted_documents, start=1):
            token_count = text.tiktoken_len(document["content"])
            if token_count > self.docs_max_total_tokens:
                sorted_documents.pop(i - 1)
                continue
            document["token_count"] = token_count
            document["doc_num"] = i

        embeddings_tokens = _docs_tiktoken_len(sorted_documents)

        self.log.print_and_log(f"context docs token count: {embeddings_tokens}")
        iterations = 0
        original_documents_count = len(sorted_documents)
        while embeddings_tokens > self.docs_max_total_tokens:
            if iterations >= original_documents_count:
                break
            # Find the index of the document with the highest token_count that exceeds ceq_docs_max_token_length
            max_token_count_idx = max(
                (
                    idx
                    for idx, document in enumerate(sorted_documents)
                    if document["token_count"] > self.docs_max_token_length
                ),
                key=lambda idx: sorted_documents[idx]["token_count"],
                default=None,
            )
            # If a document was found that meets the conditions, remove it from the list
            if max_token_count_idx is not None:
                doc_type = sorted_documents[max_token_count_idx]["doc_type"]
                if doc_type == "soft":
                    soft_count -= 1
                else:
                    hard_count -= 1
                sorted_documents.pop(max_token_count_idx)
                break
            # Remove the lowest scoring 'soft' document if there is more than one,
            elif soft_count > 1:
                for idx, document in reversed(list(enumerate(sorted_documents))):
                    if document["doc_type"] == "soft":
                        sorted_documents.pop(idx)
                        soft_count -= 1
                        break
            # otherwise remove the lowest scoring 'hard' document
            elif hard_count > 1:
                for idx, document in reversed(list(enumerate(sorted_documents))):
                    if document["doc_type"] == "hard":
                        sorted_documents.pop(idx)
                        hard_count -= 1
                        break
            else:
                # Find the index of the document with the highest token_count
                max_token_count_idx = max(
                    range(len(sorted_documents)),
                    key=lambda idx: sorted_documents[idx]["token_count"],
                )
                # Remove the document with the highest token_count from the list
                sorted_documents.pop(max_token_count_idx)

            embeddings_tokens = _docs_tiktoken_len(sorted_documents)
            self.log.print_and_log("removed lowest scoring embedding doc .")
            self.log.print_and_log(f"context docs token count: {embeddings_tokens}")
            iterations += 1
        self.log.print_and_log(f"number of context docs now: {len(sorted_documents)}")
        # Same as above but removes based on total count of docs instead of token count.
        while len(sorted_documents) > self.docs_max_used:
            if soft_count > 1:
                for idx, document in reversed(list(enumerate(sorted_documents))):
                    if document["doc_type"] == "soft":
                        sorted_documents.pop(idx)
                        soft_count -= 1
                        break
            elif hard_count > 1:
                for idx, document in reversed(list(enumerate(sorted_documents))):
                    if document["doc_type"] == "hard":
                        sorted_documents.pop(idx)
                        hard_count -= 1
                        break
            # sself.log.print_and_log("removed lowest scoring embedding doc.")

        for i, document in enumerate(sorted_documents, start=1):
            document["doc_num"] = i

        return sorted_documents

    def ceq_append_meta(self, input_text, parsed_documents):
        # Covering LLM doc notations cases
        # The modified pattern now includes optional opening parentheses or brackets before "Document"
        # and optional closing parentheses or brackets after the number
        pattern = r"[\[\(]?Document\s*\[?(\d+)\]?\)?[\]\)]?"
        formatted_text = re.sub(pattern, r"[\1]", input_text, flags=re.IGNORECASE)

        # This finds all instances of [n] in the LLM response
        pattern_num = r"\[\d\]"
        matches = re.findall(pattern_num, formatted_text)
        print(matches)

        if not matches:
            self.log.print_and_log("No supporting docs.")
            answer_obj = {
                "answer_text": input_text,
                "llm": self.main_prompt_llm_model,
                "documents": [],
            }
            return answer_obj
        print(matches)

        # Formatted text has all mutations of documents n replaced with [n]
        answer_obj = {
            "answer_text": formatted_text,
            "llm": self.main_prompt_llm_model,
            "documents": [],
        }

        if matches:
            # Creates a lit of each unique mention of [n] in LLM response
            unique_doc_nums = set([int(match[1:-1]) for match in matches])
            for doc_num in unique_doc_nums:
                # doc_num given to llm has an index starting a 1
                # Subtract 1 to get the correct index in the list
                doc_index = doc_num - 1
                # Access the document from the list using the index
                if 0 <= doc_index < len(parsed_documents):
                    document = {
                        "doc_num": parsed_documents[doc_index]["doc_num"],
                        "url": parsed_documents[doc_index]["url"].replace(" ", "-"),
                        "title": parsed_documents[doc_index]["title"],
                    }
                    answer_obj["documents"].append(document)
                else:
                    pass
                    self.log.print_and_log(f"Document{doc_num} not found in the list.")

        self.log.print_and_log(f"response with metadata: {answer_obj}")

        return answer_obj
