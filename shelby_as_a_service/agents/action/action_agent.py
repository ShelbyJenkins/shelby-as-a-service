# region
import json
import os
import re
import traceback

import openai
import pinecone
import tiktoken
import yaml
from models.agent_models import ActionAgentModel
from services.providers.llm_service import LLMService
from services.utils.log_service import Logger
from utils.app_base import AppBase

# endregion


class ActionAgent(ModuleBase):
    # ActionAgent
    action_llm_model: str = "gpt-4"
    # QueryAgent

    ceq_data_domain_constraints_enabled: bool = False

    # APIAgent
    # api_agent_select_operation_id_llm_model: str = 'gpt-4'
    # api_agent_create_function_llm_model: str = 'gpt-4'
    # api_agent_populate_function_llm_model: str = 'gpt-4'

    service_name_: str = "action_agent"

    # Overwrite the AppBase model

    def __init__(self, config, sprite_name):
        """Initialized like any other service from sprites.
        However, non-sprite services have the option to also load as modules:
        They can take a config from a config dict service_config,
        or by setting variables with **kwargs.
        """
        super().__init__()
        self.setup_instance_config(config, sprite_name)
        self.log = Logger(
            AppBase.app_name,
            "CEQAgent",
            "ceq_agent.md",
            level="INFO",
        )

    def action_prompt_template(self, query):
        # Chooses workflow
        # Currently disabled
        with open(
            os.path.join("shelby_as_service/prompt_templates/", "action_topic_constraint.yaml"),
            "r",
            encoding="utf-8",
        ) as stream:
            # Load the YAML data and print the result
            prompt_template = yaml.safe_load(stream)

        # Loop over the list of dictionaries in data['prompt_template']
        for role in prompt_template:
            if role["role"] == "user":  # If the 'role' is 'user'
                role["content"] = query  # Replace the 'content' with 'prompt_message'

        return prompt_template

    def action_prompt_llm(self, prompt, actions):
        # Shamelessly copied from https://github.com/minimaxir/simpleaichat/blob/main/PROMPTS.md#tools
        # Creates a dic of tokens equivalent to 0-n where n is the number of action items with a logit bias of 100
        # This forces GPT to choose one.
        logit_bias_weight = 100
        logit_bias = {str(k): logit_bias_weight for k in range(15, 15 + len(actions) + 1)}

        response = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            model=self.config.action_llm_model,
            messages=prompt,
            max_tokens=1,
            logit_bias=logit_bias,
        )

        return response["choices"][0]["message"]["content"]

    def action_decision(self, query):
        prompt_template = self.action_prompt_template(query)
        actions = ["questions_on_docs", "function_calling"]
        workflow = self.action_prompt_llm(prompt_template, actions)
        return workflow

    def data_domain_decision(self, query):
        # Chooses topic
        # If no matching topic found, returns 0.
        with open(
            os.path.join("shelby_as_service/prompt_templates/", "action_topic_constraint.yaml"),
            "r",
            encoding="utf-8",
        ) as stream:
            prompt_template = yaml.safe_load(stream)

        # Create a list of formatted strings, each with the format "index. key: value"
        if isinstance(self.data_domains, dict):
            content_strs = [
                f"{index + 1}. {key}: {value}"
                for index, (key, value) in enumerate(self.data_domains.items())
            ]

        # Join the strings together with spaces between them
        topics_str = " ".join(content_strs)

        # Append the documents string to the query
        prompt_message = "user query: " + query + " topics: " + topics_str

        # Loop over the list of dictionaries in data['prompt_template']
        for role in prompt_template:
            if role["role"] == "user":
                role["content"] = prompt_message

        logit_bias_weight = 100
        logit_bias = {str(k): logit_bias_weight for k in range(15, 15 + len(self.data_domains) + 1)}

        response = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            model=self.config.ceq_data_domain_constraints_llm_model,
            messages=prompt_template,
            max_tokens=1,
            logit_bias=logit_bias,
        )

        domain_response = self.ceq_agent.check_response(response)
        if not domain_response:
            return None

        domain_key = int(domain_response)

        if domain_key == 0:
            return 0
        # Otherwise return string with the namespace of the domain in the vectorstore
        domain_name = list(self.data_domains.keys())[
            domain_key - 1
        ]  # We subtract 1 because list indices start at 0

        self.ceq_agent.log.info(
            f"{self.config.ceq_data_domain_constraints_llm_model} chose to fetch context docs from {domain_name} data domain."
        )

        return domain_name

    def select_data_domain(self, query):
        response = None

        if len(self.data_domains) == 0:
            self.log.info(f"Error: no enabled data domains for moniker: {self.moniker_name}")
            return
        elif len(self.data_domains) == 1:
            # If only one topic, then we skip the ActionAgent topic decision.
            for key, _ in self.data_domains.items():
                domain_name = key
        else:
            domain_name = self.action_agent.data_domain_decision(query)

        # If no domain found message is sent to sprite
        if domain_name == 0:
            response = self.ceq_data_domain_none_found_message
            response += "\n"
            for key, value in self.data_domains.items():
                response += f"{key}: {value}\n"
            self.log.info(response)

        return domain_name, response

    def keyword_generator(self, query):
        with open(
            os.path.join("shelby_as_service/prompt_templates/", "ceq_keyword_generator.yaml"),
            "r",
            encoding="utf-8",
        ) as stream:
            # Load the YAML data and print the result
            prompt_template = yaml.safe_load(stream)

        # Loop over the list of dictionaries in data['prompt_template']
        for role in prompt_template:
            if role["role"] == "user":  # If the 'role' is 'user'
                role["content"] = query  # Replace the 'content' with 'prompt_message'

        response = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            model=self.ceq_keyword_generator_llm_model,
            messages=prompt_template,
            max_tokens=25,
        )

        keyword_generator_response = self.check_response(response)
        if not keyword_generator_response:
            return None

        generated_keywords = f"query: {query}, keywords: {keyword_generator_response}"

        return generated_keywords

    @staticmethod
    def doc_relevancy_check(query, documents):
        returned_documents_list = []
        for returned_doc in documents:
            returned_documents_list.append(returned_doc["url"])
        self.log.info(
            f"{len(documents)} documents returned from vectorstore: {returned_documents_list}"
        )
        with open(
            os.path.join("shelby_as_service/prompt_templates/", "ceq_doc_check.yaml"),
            "r",
            encoding="utf-8",
        ) as stream:
            # Load the YAML data and print the result
            prompt_template = yaml.safe_load(stream)

        doc_counter = 1
        content_strs = []
        documents_str = ""
        for doc in documents:
            content_strs.append(f"{doc['title']} doc_number: [{doc_counter}]")
            documents_str = " ".join(content_strs)
            doc_counter += 1
        prompt_message = "Query: " + query + " Documents: " + documents_str

        logit_bias_weight = 100
        # 0-9
        logit_bias = {str(k): logit_bias_weight for k in range(15, 15 + len(documents) + 1)}
        # \n
        logit_bias["198"] = logit_bias_weight

        # Loop over the list of dictionaries in data['prompt_template']
        for role in prompt_template:
            if role["role"] == "user":  # If the 'role' is 'user'
                role["content"] = prompt_message  # Replace the 'content' with 'prompt_message'

        response = openai.ChatCompletion.create(
            api_key=self.secrets["openai_api_key"],
            model=self.ceq_doc_relevancy_check_llm_model,
            messages=prompt_template,
            max_tokens=10,
            logit_bias=logit_bias,
        )

        doc_check = self.check_response(response)
        if not doc_check:
            return None

        # This finds all instances of n in the LLM response
        pattern_num = r"\d"
        matches = re.findall(pattern_num, doc_check)

        if (len(matches) == 1 and matches[0] == "0") or len(matches) == 0:
            self.log.info(f"Error in doc_check: {response}")
            return None

        relevant_documents = []
        # Creates a list of each unique mention of n in LLM response
        unique_doc_nums = set([int(match) for match in matches])
        for doc_num in unique_doc_nums:
            # doc_num given to llm has an index starting a 1
            # Subtract 1 to get the correct index in the list
            # Access the document from the list using the index
            relevant_documents.append(documents[doc_num - 1])

        for returned_doc in relevant_documents:
            returned_documents_list.append(returned_doc["url"])
        self.log.info(
            f"{len(relevant_documents)} documents returned from doc_check: {returned_documents_list}"
        )
        if not relevant_documents:
            self.log.info("No supporting documents after doc_relevancy_check!")
            return None

        return relevant_documents
