# region
import os
import traceback
import json, yaml, re
import openai, pinecone, tiktoken
from typing import Dict, Optional, List, Any
import modules.utils.config_manager as ConfigManager
from agents.agent_base import AgentBase
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from services.database_service import DatabaseService
import modules.text_processing.text as text

# endregion


class CEQAgent(AgentBase):
    agent_name: str = "ceq_agent"
    app: Optional[Any] = None
    index: Optional[Any] = None
    llm_provider: str = "openai_llm"
    llm_model: str = "gpt-4"
    data_domain_constraints_enabled: bool = False
    data_domain_constraints_llm_model: str = "gpt-4"
    data_domain_none_found_message: str = "Query not related to any supported data domains (aka topics). Supported data domains are:"
    keyword_generator_enabled: bool = False
    keyword_generator_llm_model: str = "gpt-4"
    doc_relevancy_check_enabled: bool = False
    doc_relevancy_check_llm_model: str = "gpt-4"
    docs_to_retrieve: int = 5
    docs_max_token_length: int = 1200
    docs_max_total_tokens: int = 3500
    docs_max_used: int = 5

    def __init__(self, parent_sprite=None):
        super().__init__(parent_sprite=parent_sprite)
        ConfigManager.setup_service_config(self)
        self.llm_service = LLMService(self)

        self.embedding_service = EmbeddingService(self)

        self.database_service = DatabaseService(self)

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

    def ceq_main_prompt_template(self, query, documents=None):
        with open(
            os.path.join(
                "shelby_as_a_service/modules/prompt_templates/", "ceq_main_prompt.yaml"
            ),
            "r",
            encoding="utf-8",
        ) as stream:
            # Load the YAML data and print the result
            prompt_template = yaml.safe_load(stream)

        # Loop over documents and append them to each other and then adds the query
        if documents:
            content_strs = []
            for doc in documents:
                doc_num = doc["doc_num"]
                content_strs.append(f"{doc['content']} doc_num: [{doc_num}]")
                documents_str = " ".join(content_strs)
            prompt_message = "Query: " + query + " Documents: " + documents_str
        else:
            prompt_message = "Query: " + query

        # Loop over the list of dictionaries in data['prompt_template']
        for role in prompt_template:
            if role["role"] == "user":  # If the 'role' is 'user'
                role[
                    "content"
                ] = prompt_message  # Replace the 'content' with 'prompt_message'

        # self.log.print_and_log(f"prepared prompt: {json.dumps(prompt_template, indent=4)}")

        return prompt_template

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

    def run_context_enriched_query(
        self, query, stream=False, provider_name=None, model_name=None
    ):
        # try:
        data_domain_name = None
        if self.data_domain_constraints_enabled:
            data_domain_name, response = self.select_data_domain(query)
            if response is not None:
                return response

        self.log.print_and_log(f"Running query: {query}")

        if self.keyword_generator_enabled:
            generated_keywords = self.action_agent.keyword_generator(query)
            self.log.print_and_log(
                f"ceq_keyword_generator response: {generated_keywords}"
            )
            search_terms = self.embedding_service.get_query_embedding(
                generated_keywords
            )
        else:
            search_terms = self.embedding_service.get_query_embedding(query)
        self.log.print_and_log("Embeddings retrieved")

        returned_documents = self.database_service.query_index(
            search_terms, self.docs_to_retrieve, data_domain_name
        )

        prepared_documents = self.doc_handling(returned_documents)

        if not prepared_documents:
            return "No supporting documents found. Currently we don't support queries without supporting context."
        else:
            prompt = self.ceq_main_prompt_template(query, prepared_documents)

        self.log.print_and_log("Sending prompt to LLM")
        if stream:
            yield from self.llm_service.create_streaming_chat(
                prompt,
                provider_name=provider_name
                if provider_name is not None
                else self.llm_provider,
                model_name=model_name if model_name is not None else self.llm_model,
            )
        else:
            llm_response = self.llm_service.create_chat(
                prompt,
                provider_name=provider_name
                if provider_name is not None
                else self.llm_provider,
                model_name=model_name if model_name is not None else self.llm_model,
            )
            parsed_response = self.ceq_append_meta(llm_response, prepared_documents)
            self.log.print_and_log(
                f"LLM response with appended metadata: {json.dumps(parsed_response, indent=4)}"
            )

            return parsed_response

        # except Exception as error:
        #     # Logs error and sends error to sprite
        #     error_message = f"An error occurred while processing request: {error}\n"
        #     error_message += "Traceback (most recent call last):\n"
        #     error_message += traceback.format_exc()

        #     self.log.print_and_log(error_message)
        #     print(error_message)
        #     return error_message
        #     # return f"Bot broke. Probably just an API issue. Feel free to try again. Otherwise contact support."
