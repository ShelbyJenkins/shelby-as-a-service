import os
from typing import Literal, Optional

import services.text_processing.text_utils as text_utils
import yaml
from context_index.doc_index.docs.context_docs import RetrievalDoc


def create_openai_prompt(
    user_input: Optional[str] = None,
    prompt_string: Optional[str] = None,
    prompt_template_path: Optional[str] = None,
    context_docs: Optional[list[RetrievalDoc] | list[str] | str] = None,
) -> list[dict[str, str]]:
    system_prompt = load_prompt_template(
        prompt_template_path=prompt_template_path, prompt_string=prompt_string
    )
    if not user_input:
        user_input = ""
    if context_docs:
        document_string = create_document_string(context_docs)
        user_content = "Documents: " + document_string + user_input
    else:
        user_content = user_input

    return [
        {"role": "system", "content": system_prompt},
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


def create_document_string(context_docs: list[RetrievalDoc] | list[str] | str):
    content_strs = []
    if isinstance(context_docs, str):
        context_docs = [context_docs]
    for i, doc in enumerate(context_docs):
        if isinstance(doc, RetrievalDoc):
            if doc.retrieval_rank:
                doc_num = doc.retrieval_rank
            else:
                doc_num = i
            context_chunk = doc.context_chunk
        else:
            doc_num = i
            context_chunk = doc

        document_content = text_utils.clean_text_content(context_chunk)

        content_strs.append(f"{document_content} doc_num: [{doc_num}]")

    return " ".join(content_strs)


def load_prompt_template(
    prompt_string: Optional[str] = None,
    prompt_template_path: Optional[str] = None,
) -> str:
    if prompt_string and prompt_template_path:
        raise ValueError("prompt_string and prompt_template_path cannot both be used.")
    if prompt_template_path:
        with open(
            prompt_template_path,
            "r",
            encoding="utf-8",
        ) as stream:
            if prompt_template := (yaml.safe_load(stream)):
                system_prompt = prompt_template
            else:
                raise ValueError(f"prompt_template_path '{prompt_template_path}' is empty.")
    elif prompt_string:
        system_prompt = prompt_string
    else:
        raise ValueError("prompt_string and prompt_template_path cannot both be None.")

    if not isinstance(system_prompt, str):
        raise ValueError("prompt_template should be a string.")
    if not system_prompt:
        system_prompt = "Answer in peace my friend."

    return system_prompt
