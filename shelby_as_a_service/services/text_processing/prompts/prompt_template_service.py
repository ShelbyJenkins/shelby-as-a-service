import os
from typing import Dict

import services.text_processing.text_utils as text_utils
import yaml


def create_openai_prompt(query, prompt_template_path, context_docs=None) -> list[dict[str, str]]:
    prompt_template = load_prompt_template(prompt_template_path)
    document_string = create_document_string(context_docs)
    if query:
        user_content = "Query: " + query
    else:
        user_content = ""
    if document_string:
        user_content = "Documents: " + document_string + query

    if prompt_template is None:
        prompt_template = ""
    return [
        {"role": "system", "content": prompt_template},
        {"role": "user", "content": user_content},
    ]


def tiktoken_len_of_openai_prompt(prompt, llm_model_instance) -> int:
    num_tokens = 0
    for message in prompt:
        num_tokens += llm_model_instance.TOKENS_PER_MESSAGE
        for key, value in message.items():
            num_tokens += text_utils.tiktoken_len(value, llm_model_instance.MODEL_NAME)
            if key == "name":
                num_tokens += llm_model_instance.TOKENS_PER_NAME
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def create_document_string(documents=None):
    if documents is None:
        return None

    if isinstance(documents, str):
        return text_utils.clean_text_content(documents)

    content_strs = []

    for i, doc in enumerate(documents):
        if document_number := getattr(doc, "doc_num", None):
            doc_num = document_number
        elif document_number := doc.get("doc_num", None):
            doc_num = document_number
        else:
            doc_num = i
        document_content = text_utils.extract_document_content(doc)
        document_content = text_utils.clean_text_content(document_content)

        content_strs.append(f"{document_content} doc_num: [{doc_num}]")

    return " ".join(content_strs)


def load_prompt_template(prompt_template_path):
    if prompt_template_path is None:
        return None
    with open(
        prompt_template_path,
        "r",
        encoding="utf-8",
    ) as stream:
        # Load the YAML data and print the result
        if prompt_template := (yaml.safe_load(stream)):
            return prompt_template
        print("prompt template didn't load")

        return "Answer in peace my friend."